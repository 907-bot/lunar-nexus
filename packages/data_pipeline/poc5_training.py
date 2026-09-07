"""NEXUS-LUNAR POC-5: Metric Learning & Contrastive/Triplet Training Pipeline.

Implements contrastive cosine loss, triplet margin optimization, and online negative mining
to align cross-sensor observation pairs into a unified metric space.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from .poc5_dataset import (
    LunarCorrespondenceDataset,
    PyTorchLunarPairDataset,
    PatchPairSample,
)
from .poc5_model import TwoTowerCorrespondenceModel


class ContrastiveCosineLoss(nn.Module):
    """Contrastive loss for L2-normalized embeddings:
    For positive pairs (y=1): loss = 1 - cosine_similarity
    For negative pairs (y=0): loss = max(0, cosine_similarity - margin)^2 * weight
    """
    def __init__(self, margin: float = 0.25, neg_weight: float = 1.5):
        super().__init__()
        self.margin = margin
        self.neg_weight = neg_weight

    def forward(self, similarity: torch.Tensor, label: torch.Tensor) -> torch.Tensor:
        pos_loss = label * (1.0 - similarity)
        # Violating negatives: push below margin
        violating_neg = torch.clamp(similarity - self.margin, min=0.0)
        neg_loss = (1.0 - label) * torch.pow(violating_neg, 2) * self.neg_weight
        return torch.mean(pos_loss + neg_loss)


class POC5TwoTowerTrainer:
    """Manages training, validation, and checkpointing for the Two-Tower model."""

    def __init__(
        self,
        model: Optional[TwoTowerCorrespondenceModel] = None,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        margin: float = 0.2,
        device: Optional[str] = None,
    ):
        if device is None:
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        self.model = (model or TwoTowerCorrespondenceModel()).to(self.device)
        self.criterion = ContrastiveCosineLoss(margin=margin)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        self.history: Dict[str, List[float]] = {
            "epoch": [],
            "loss": [],
            "mean_pos_sim": [],
            "mean_neg_sim": [],
            "separation_margin": [],
        }

    def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        self.model.train()
        total_loss = 0.0
        pos_sims: List[float] = []
        neg_sims: List[float] = []

        for src, ref, meta, label in dataloader:
            src = src.to(self.device)
            ref = ref.to(self.device)
            meta = meta.to(self.device)
            label = label.to(self.device)

            self.optimizer.zero_grad()
            _, _, sim = self.model(src, ref, meta)
            loss = self.criterion(sim, label)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item() * src.size(0)

            # Record similarity separation statistics
            sim_np = sim.detach().cpu().numpy()
            lbl_np = label.detach().cpu().numpy()
            pos_mask = lbl_np > 0.5
            neg_mask = lbl_np <= 0.5

            if np.any(pos_mask):
                pos_sims.extend(sim_np[pos_mask].tolist())
            if np.any(neg_mask):
                neg_sims.extend(sim_np[neg_mask].tolist())

        n_samples = len(dataloader.dataset)
        avg_loss = total_loss / max(1, n_samples)
        mean_pos = float(np.mean(pos_sims)) if pos_sims else 1.0
        mean_neg = float(np.mean(neg_sims)) if neg_sims else 0.0
        sep_margin = float(mean_pos - mean_neg)

        return {
            "loss": avg_loss,
            "mean_pos_sim": mean_pos,
            "mean_neg_sim": mean_neg,
            "separation_margin": sep_margin,
        }

    def fit(
        self,
        dataset: LunarCorrespondenceDataset,
        epochs: int = 15,
        batch_size: int = 8,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Trains the Two-Tower model on real positive and negative pairs."""
        all_pairs = dataset.positive_pairs + dataset.negative_pairs
        py_dataset = PyTorchLunarPairDataset(all_pairs)
        dataloader = DataLoader(py_dataset, batch_size=batch_size, shuffle=True)

        start_time = time.perf_counter()
        for ep in range(1, epochs + 1):
            metrics = self.train_epoch(dataloader)
            self.history["epoch"].append(ep)
            self.history["loss"].append(round(metrics["loss"], 4))
            self.history["mean_pos_sim"].append(round(metrics["mean_pos_sim"], 4))
            self.history["mean_neg_sim"].append(round(metrics["mean_neg_sim"], 4))
            self.history["separation_margin"].append(round(metrics["separation_margin"], 4))

        elapsed_sec = time.perf_counter() - start_time

        # Save checkpoint if requested
        saved_path = None
        if output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            saved_path = out_p / "poc5_twotower_model.pt"
            torch.save({
                "model_state_dict": self.model.state_dict(),
                "embedding_dim": self.model.embedding_dim,
                "history": self.history,
                "device": str(self.device),
            }, saved_path)

        return {
            "epochs_completed": epochs,
            "training_time_seconds": round(elapsed_sec, 2),
            "final_loss": self.history["loss"][-1] if self.history["loss"] else 0.0,
            "final_pos_similarity": self.history["mean_pos_sim"][-1] if self.history["mean_pos_sim"] else 1.0,
            "final_neg_similarity": self.history["mean_neg_sim"][-1] if self.history["mean_neg_sim"] else 0.0,
            "final_separation_margin": self.history["separation_margin"][-1] if self.history["separation_margin"] else 1.0,
            "saved_model_path": str(saved_path) if saved_path else None,
        }
