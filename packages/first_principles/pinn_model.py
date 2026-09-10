"""Physics-Informed Neural Network (PINN) Module for NEXUS-LUNAR.
Couples deep neural network representations with governing partial differential equations (PDEs)
for lunar thermal diffusion, volatile ice preservation, and electromagnetic wave mechanics.
"""

from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import torch
import torch.nn as nn


class LunarThermalPINN(nn.Module):
    """Physics-Informed Neural Network (PINN) solving 1D Lunar Regolith Thermal Diffusion.
    Governing PDE:
        dT/dt - alpha * d^2T/dz^2 = 0
    where:
        T(t, z) is temperature (Kelvin)
        t is time across synodic lunar month (seconds)
        z is depth beneath regolith (meters)
        alpha = k / (rho * c_p) is thermal diffusivity (m^2/s)
    """

    def __init__(self, hidden_dim: int = 64, num_layers: int = 4):
        super().__init__()
        layers = []
        # Input features: (t_norm, z_norm) in [0, 1]
        in_dim = 2
        for i in range(num_layers):
            out_dim = hidden_dim
            layers.append(nn.Linear(in_dim if i == 0 else hidden_dim, out_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))  # Output: Predicted Temperature T(t, z)
        self.net = nn.Sequential(*layers)

        # Scale constants
        self.t_scale = 29.530589 * 86400.0  # 1 synodic month in seconds (~2.55e6 s)
        self.z_scale = 2.0                   # Max depth modeled (2.0 meters)
        self.t_mean = 137.5                  # Mean polar surface temperature (K)
        self.t_amp = 92.5                    # Diurnal amplitude (K)

    def forward(self, t: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        """Forward pass predicting temperature T in Kelvin.
        t: tensor of shape (N, 1) in seconds [0, t_scale]
        z: tensor of shape (N, 1) in meters [0, z_scale]
        """
        # Normalize inputs to [0, 1]
        t_norm = t / self.t_scale
        z_norm = z / self.z_scale
        inputs = torch.cat([t_norm, z_norm], dim=-1)
        raw_out = self.net(inputs)
        t_pred = self.t_mean + self.t_amp * raw_out
        return t_pred

    def compute_pde_residual(
        self,
        t: torch.Tensor,
        z: torch.Tensor,
        thermal_diffusivity: float = 1.442e-8,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Calculates PDE residual via PyTorch automatic differentiation (autograd).
        Residual R = dT/dt - alpha * d^2T/dz^2
        """
        t = t.clone().requires_grad_(True)
        z = z.clone().requires_grad_(True)

        T = self.forward(t, z)

        # 1st-order temporal derivative dT/dt
        grad_t = torch.autograd.grad(
            outputs=T,
            inputs=t,
            grad_outputs=torch.ones_like(T),
            create_graph=True,
            retain_graph=True,
        )[0]

        # 1st-order spatial gradient dT/dz
        grad_z = torch.autograd.grad(
            outputs=T,
            inputs=z,
            grad_outputs=torch.ones_like(T),
            create_graph=True,
            retain_graph=True,
        )[0]

        # 2nd-order spatial curvature d^2T/dz^2
        grad_zz = torch.autograd.grad(
            outputs=grad_z,
            inputs=z,
            grad_outputs=torch.ones_like(grad_z),
            create_graph=True,
            retain_graph=True,
        )[0]

        # Governing Heat PDE Residual
        residual = grad_t - thermal_diffusivity * grad_zz
        return residual, T

    def compute_loss(
        self,
        t_colloc: torch.Tensor,
        z_colloc: torch.Tensor,
        t_bc: torch.Tensor,
        t_bc_true: torch.Tensor,
        alpha: float = 1.442e-8,
        lambda_pde: float = 1.0,
    ) -> Dict[str, torch.Tensor]:
        """Calculates total multi-objective PINN loss:
        L_total = L_boundary + lambda_pde * L_pde
        """
        # Boundary condition loss at surface z = 0
        z_zero = torch.zeros_like(t_bc)
        t_surf_pred = self.forward(t_bc, z_zero)
        loss_bc = torch.mean((t_surf_pred - t_bc_true) ** 2)

        # Collocation physics residual loss
        res, _ = self.compute_pde_residual(t_colloc, z_colloc, thermal_diffusivity=alpha)
        loss_pde = torch.mean((res * self.t_scale) ** 2)

        total_loss = loss_bc + lambda_pde * loss_pde

        return {
            "total_loss": total_loss,
            "loss_bc": loss_bc,
            "loss_pde": loss_pde,
            "pde_residual_rms": torch.sqrt(torch.mean(res ** 2)),
        }


class LunarMultiphysicsPINN:
    """High-level controller and fast-inference solver for Lunar PINN modeling."""

    def __init__(self, hidden_dim: int = 64, num_layers: int = 3):
        self.model = LunarThermalPINN(hidden_dim=hidden_dim, num_layers=num_layers)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        self.device = torch.device("cpu")
        self.model.to(self.device)

    def train_step(self, num_collocation_pts: int = 256) -> Dict[str, float]:
        """Performs a single gradient descent optimization step on collocation points."""
        self.model.train()
        self.optimizer.zero_grad()

        # Random collocation points in domain
        t_colloc = torch.rand(num_collocation_pts, 1, device=self.device) * self.model.t_scale
        z_colloc = torch.rand(num_collocation_pts, 1, device=self.device) * self.model.z_scale

        # Surface Boundary Condition: T(t, 0) = 137.5 + 92.5 * cos(2*pi*t / P)
        omega = 2.0 * math.pi / self.model.t_scale
        t_bc = torch.rand(64, 1, device=self.device) * self.model.t_scale
        t_bc_true = self.model.t_mean + self.model.t_amp * torch.cos(omega * t_bc)

        losses = self.model.compute_loss(t_colloc, z_colloc, t_bc, t_bc_true, lambda_pde=0.01)
        losses["total_loss"].backward()
        self.optimizer.step()

        return {
            "total_loss": round(float(losses["total_loss"].item()), 6),
            "loss_bc": round(float(losses["loss_bc"].item()), 6),
            "loss_pde": round(float(losses["loss_pde"].item()), 6),
            "pde_residual_rms": round(float(losses["pde_residual_rms"].item()), 8),
        }

    def predict_temperature_field(
        self,
        time_fraction: float = 0.5,
        depth_steps: int = 15,
        max_depth_m: float = 1.5,
    ) -> Dict[str, Any]:
        """Evaluates PINN prediction across regolith depth at a given time in synodic cycle."""
        self.model.eval()
        t_sec = float(time_fraction) * self.model.t_scale
        depths = torch.linspace(0.0, max_depth_m, depth_steps, device=self.device).view(-1, 1)
        times = torch.full_like(depths, t_sec)

        with torch.no_grad():
            t_pred = self.model(times, depths).view(-1).cpu().numpy()

        results = []
        is_cold_trap = False
        for z_val, t_val in zip(depths.view(-1).cpu().numpy(), t_pred):
            z_cm = round(float(z_val * 100.0), 1)
            temp_k = round(float(t_val), 2)
            stable = temp_k <= 110.0
            if stable and z_val > 0.1:
                is_cold_trap = True
            results.append({
                "depth_cm": z_cm,
                "predicted_temp_k": temp_k,
                "ice_stable": stable,
            })

        return {
            "time_in_lunar_day_fraction": time_fraction,
            "depth_profile": results,
            "subsurface_cold_trap_detected": is_cold_trap,
            "pinn_architecture": f"MLP-{len(self.model.net)}Layers-Tanh-Autograd",
            "governing_pde": "dT/dt - alpha * d^2T/dz^2 = 0",
        }
