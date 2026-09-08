"""NEXUS-LUNAR POC-7: Spatial Knowledge Graph Engine.

Provides an offline-first, in-memory, structured graph abstraction for lunar spatial
knowledge representation. Supports typed nodes, typed edges, stable deterministic IDs,
provenance preservation, graph query capabilities, and graph algorithms
(neighborhood expansion, connected components, shortest paths).

Exportable to structured JSON (nodes.json, edges.json, poc7_knowledge_graph.json)
and fully compatible with future Neo4j property-graph ingest.
"""

from __future__ import annotations
import json
from collections import deque, defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Union

from packages.data_pipeline.poc7_models import (
    NodeType,
    RelationType,
    GraphNode,
    GraphEdge,
    ProvenanceRecord,
)


class SpatialKnowledgeGraph:
    """Offline-first Lunar Spatial Knowledge Graph with graph query & algorithm engine."""

    def __init__(self, name: str = "NEXUS_LUNAR_SPATIAL_GRAPH"):
        self.name = name
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        # Adjacency indexes for fast lookups
        self._adj_out: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._adj_in: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._type_index: Dict[str, Set[str]] = defaultdict(set)

    def add_node(
        self,
        node_id: str,
        node_type: Union[NodeType, str],
        properties: Optional[Dict[str, Any]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        """Add or update a node in the graph with stable ID and type indexing."""
        nt = node_type if isinstance(node_type, NodeType) else NodeType(node_type)
        props = properties or {}
        prov = provenance or {}

        node = GraphNode(id=node_id, type=nt, properties=props, provenance=prov)
        self.nodes[node_id] = node
        self._type_index[nt.value].add(node_id)
        return node

    def add_edge(
        self,
        source_id: str,
        relationship: Union[RelationType, str],
        target_id: str,
        properties: Optional[Dict[str, Any]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> GraphEdge:
        """Add a directed edge between two existing nodes with provenance."""
        rel = relationship if isinstance(relationship, RelationType) else RelationType(relationship)
        props = properties or {}
        prov = provenance or {}

        edge = GraphEdge(
            source=source_id,
            relationship=rel,
            target=target_id,
            properties=props,
            provenance=prov,
        )
        self.edges.append(edge)
        self._adj_out[source_id].append(edge)
        self._adj_in[target_id].append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieve node by stable ID."""
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: Union[NodeType, str]) -> List[GraphNode]:
        """Retrieve all nodes belonging to a specific node type."""
        nt_val = node_type.value if isinstance(node_type, NodeType) else str(node_type)
        ids = self._type_index.get(nt_val, set())
        return [self.nodes[nid] for nid in ids if nid in self.nodes]

    def get_outgoing_edges(self, node_id: str, relationship: Optional[Union[RelationType, str]] = None) -> List[GraphEdge]:
        """Get outgoing edges from node, optionally filtered by relationship type."""
        edges = self._adj_out.get(node_id, [])
        if relationship is None:
            return edges
        rel_val = relationship.value if isinstance(relationship, RelationType) else str(relationship)
        return [e for e in edges if (e.relationship.value if isinstance(e.relationship, RelationType) else str(e.relationship)) == rel_val]

    def get_incoming_edges(self, node_id: str, relationship: Optional[Union[RelationType, str]] = None) -> List[GraphEdge]:
        """Get incoming edges to node, optionally filtered by relationship type."""
        edges = self._adj_in.get(node_id, [])
        if relationship is None:
            return edges
        rel_val = relationship.value if isinstance(relationship, RelationType) else str(relationship)
        return [e for e in edges if (e.relationship.value if isinstance(e.relationship, RelationType) else str(e.relationship)) == rel_val]

    # =========================================================================
    # SPECIALIZED SPATIAL GRAPH QUERIES
    # =========================================================================

    def find_observations_for_region(self, region_id: str) -> List[GraphNode]:
        """Find all observation nodes contained within or associated with a lunar region."""
        out_edges = self.get_outgoing_edges(region_id, RelationType.CONTAINS)
        obs_nodes = []
        for e in out_edges:
            target = self.get_node(e.target)
            if target and target.type in (NodeType.OBSERVATION, NodeType.IMAGE, NodeType.TERRAIN_PATCH):
                obs_nodes.append(target)
        return obs_nodes

    def find_registered_correspondences(self) -> List[Dict[str, Any]]:
        """Find verified registered correspondences between terrain patches."""
        correspondences = []
        for edge in self.edges:
            rel_str = edge.relationship.value if isinstance(edge.relationship, RelationType) else str(edge.relationship)
            if rel_str == RelationType.CORRESPONDS_TO.value:
                src_node = self.get_node(edge.source)
                tgt_node = self.get_node(edge.target)
                correspondences.append({
                    "source_id": edge.source,
                    "target_id": edge.target,
                    "source_properties": src_node.properties if src_node else {},
                    "target_properties": tgt_node.properties if tgt_node else {},
                    "registration_properties": edge.properties,
                    "provenance": edge.provenance,
                })
        return correspondences

    def find_patches_near_crater(self, crater_id: str, max_distance_m: Optional[float] = None) -> List[Dict[str, Any]]:
        """Find terrain patches located near a specified crater."""
        in_edges = self.get_incoming_edges(crater_id, RelationType.LOCATED_NEAR)
        results = []
        for e in in_edges:
            dist = e.properties.get("distance_to_crater_m", 0.0)
            if max_distance_m is not None and dist > max_distance_m:
                continue
            patch = self.get_node(e.source)
            if patch:
                results.append({
                    "patch_id": patch.id,
                    "distance_m": dist,
                    "crater_id": crater_id,
                    "patch_properties": patch.properties,
                })
        return results

    def find_illuminated_patches(self, min_illumination: float = 0.5) -> List[GraphNode]:
        """Find terrain patches with favorable illumination."""
        matching = []
        for node in self.get_nodes_by_type(NodeType.ILLUMINATION_STATE):
            mean_illum = node.properties.get("illumination_mean", 0.0)
            state = node.properties.get("illumination_state", "")
            if mean_illum >= min_illumination or state == "ILLUMINATED":
                # Find connected terrain patch
                in_edges = self.get_incoming_edges(node.id, RelationType.HAS_ILLUMINATION)
                for e in in_edges:
                    patch = self.get_node(e.source)
                    if patch and patch not in matching:
                        matching.append(patch)
        return matching

    def find_low_light_patches(self, max_illumination: float = 0.3) -> List[GraphNode]:
        """Find terrain patches in shadowed or low-light conditions."""
        matching = []
        for node in self.get_nodes_by_type(NodeType.ILLUMINATION_STATE):
            mean_illum = node.properties.get("illumination_mean", 1.0)
            state = node.properties.get("illumination_state", "")
            if mean_illum <= max_illumination or state in ("SHADOWED", "LOW_LIGHT"):
                in_edges = self.get_incoming_edges(node.id, RelationType.HAS_ILLUMINATION)
                for e in in_edges:
                    patch = self.get_node(e.source)
                    if patch and patch not in matching:
                        matching.append(patch)
        return matching

    def find_patches_with_resource_indicators(self, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Find terrain patches associated with resource-related spectral indicators."""
        results = []
        for node in self.get_nodes_by_type(NodeType.SPECTRAL_OBSERVATION):
            score = node.properties.get("indicator_score", 0.0)
            if score >= min_score:
                in_edges = self.get_incoming_edges(node.id, RelationType.HAS_RESOURCE_INDICATOR)
                for e in in_edges:
                    patch = self.get_node(e.source)
                    if patch:
                        results.append({
                            "patch_id": patch.id,
                            "spectral_node_id": node.id,
                            "indicator_score": score,
                            "feature": node.properties.get("mineralogical_feature", "INDICATOR"),
                            "sensor": node.properties.get("sensor", "IIRS"),
                            "disclaimer": node.properties.get("disclaimer", ""),
                        })
        return results

    def find_candidate_sites(
        self,
        max_slope: Optional[float] = None,
        min_suitability: Optional[float] = None,
        exclude_critical_hazards: bool = True,
    ) -> List[GraphNode]:
        """Find candidate sites satisfying constraint parameters."""
        candidates = self.get_nodes_by_type(NodeType.CANDIDATE_SITE)
        filtered = []
        for site in candidates:
            suitability = site.properties.get("overall_suitability_score", 0.0)
            slope = site.properties.get("slope_degrees", 0.0)
            has_critical = False

            if exclude_critical_hazards:
                hazard_edges = self.get_incoming_edges(site.id, RelationType.CONSTRAINS)
                for he in hazard_edges:
                    h_node = self.get_node(he.source)
                    if h_node and h_node.properties.get("severity") == "CRITICAL":
                        has_critical = True
                        break

            if has_critical:
                continue
            if max_slope is not None and slope > max_slope:
                continue
            if min_suitability is not None and suitability < min_suitability:
                continue

            filtered.append(site)
        return sorted(filtered, key=lambda s: s.properties.get("overall_suitability_score", 0.0), reverse=True)

    def find_hazards_affecting_site(self, site_id: str) -> List[GraphNode]:
        """Find all hazard nodes constraining a specific candidate site."""
        hazard_edges = self.get_incoming_edges(site_id, RelationType.CONSTRAINS)
        hazards = []
        for e in hazard_edges:
            h_node = self.get_node(e.source)
            if h_node and h_node.type == NodeType.HAZARD:
                hazards.append(h_node)
        return hazards

    def find_contributing_observations_for_site(self, site_id: str) -> List[GraphNode]:
        """Find observation and image nodes that contributed to a candidate site's spatial intelligence."""
        site = self.get_node(site_id)
        if not site:
            return []
        patch_id = site.properties.get("patch_id")
        if not patch_id:
            return []

        contributing = []
        # Check direct observation edges
        in_edges = self.get_incoming_edges(patch_id)
        for e in in_edges:
            src = self.get_node(e.source)
            if src and src.type in (NodeType.IMAGE, NodeType.OBSERVATION):
                contributing.append(src)

        # Also check correspondences
        corr_edges = self.get_incoming_edges(patch_id, RelationType.CORRESPONDS_TO) + \
                     self.get_outgoing_edges(patch_id, RelationType.CORRESPONDS_TO)
        for ce in corr_edges:
            other_id = ce.target if ce.source == patch_id else ce.source
            other = self.get_node(other_id)
            if other and other not in contributing:
                contributing.append(other)

        return contributing

    # =========================================================================
    # GRAPH ALGORITHMS
    # =========================================================================

    def neighborhood(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Breadth-first ego network extraction up to k hops."""
        if node_id not in self.nodes:
            return {"nodes": [], "edges": []}

        visited_nodes: Set[str] = {node_id}
        visited_edges: List[GraphEdge] = []
        queue: deque = deque([(node_id, 0)])

        while queue:
            curr_id, curr_depth = queue.popleft()
            if curr_depth >= depth:
                continue

            all_edges = self._adj_out.get(curr_id, []) + self._adj_in.get(curr_id, [])
            for edge in all_edges:
                other_id = edge.target if edge.source == curr_id else edge.source
                if edge not in visited_edges:
                    visited_edges.append(edge)
                if other_id not in visited_nodes:
                    visited_nodes.add(other_id)
                    queue.append((other_id, curr_depth + 1))

        return {
            "center_node_id": node_id,
            "depth": depth,
            "nodes": [self.nodes[nid].to_dict() for nid in visited_nodes if nid in self.nodes],
            "edges": [e.to_dict() for e in visited_edges],
        }

    def connected_components(self) -> List[List[str]]:
        """Identify weakly connected components in the knowledge graph."""
        visited: Set[str] = set()
        components: List[List[str]] = []

        for node_id in self.nodes:
            if node_id not in visited:
                comp: List[str] = []
                queue: deque = deque([node_id])
                visited.add(node_id)
                while queue:
                    curr = queue.popleft()
                    comp.append(curr)
                    neighbors = [e.target for e in self._adj_out.get(curr, [])] + \
                                [e.source for e in self._adj_in.get(curr, [])]
                    for nbr in neighbors:
                        if nbr in self.nodes and nbr not in visited:
                            visited.add(nbr)
                            queue.append(nbr)
                components.append(comp)
        return components

    def shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find the shortest unweighted path between two nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        if source_id == target_id:
            return [source_id]

        queue: deque = deque([[source_id]])
        visited: Set[str] = {source_id}

        while queue:
            path = queue.popleft()
            curr = path[-1]

            neighbors = [e.target for e in self._adj_out.get(curr, [])] + \
                        [e.source for e in self._adj_in.get(curr, [])]
            for nbr in neighbors:
                if nbr == target_id:
                    return path + [nbr]
                if nbr in self.nodes and nbr not in visited:
                    visited.add(nbr)
                    queue.append(path + [nbr])
        return None

    # =========================================================================
    # EXPORT & IMPORT
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete graph structure and summary statistics."""
        node_type_counts: Dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            nt_str = n.type.value if isinstance(n.type, NodeType) else str(n.type)
            node_type_counts[nt_str] += 1

        rel_type_counts: Dict[str, int] = defaultdict(int)
        for e in self.edges:
            rel_str = e.relationship.value if isinstance(e.relationship, RelationType) else str(e.relationship)
            rel_type_counts[rel_str] += 1

        return {
            "graph_name": self.name,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_type_breakdown": dict(node_type_counts),
            "relationship_type_breakdown": dict(rel_type_counts),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }

    def export_to_files(self, output_dir: Union[str, Path]) -> Dict[str, Path]:
        """Export the knowledge graph to poc7_knowledge_graph.json, nodes.json, and edges.json."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        full_graph_file = out_path / "poc7_knowledge_graph.json"
        nodes_file = out_path / "nodes.json"
        edges_file = out_path / "edges.json"

        graph_dict = self.to_dict()

        with open(full_graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_dict, f, indent=2)

        with open(nodes_file, "w", encoding="utf-8") as f:
            json.dump(graph_dict["nodes"], f, indent=2)

        with open(edges_file, "w", encoding="utf-8") as f:
            json.dump(graph_dict["edges"], f, indent=2)

        return {
            "graph": full_graph_file,
            "nodes": nodes_file,
            "edges": edges_file,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpatialKnowledgeGraph":
        """Reconstruct SpatialKnowledgeGraph from serialized dictionary."""
        graph = cls(name=data.get("graph_name", "NEXUS_LUNAR_SPATIAL_GRAPH"))
        for nd in data.get("nodes", []):
            graph.add_node(
                node_id=nd["id"],
                node_type=nd["type"],
                properties=nd.get("properties", {}),
                provenance=nd.get("provenance", {}),
            )
        for ed in data.get("edges", []):
            graph.add_edge(
                source_id=ed["source"],
                relationship=ed["relationship"],
                target_id=ed["target"],
                properties=ed.get("properties", {}),
                provenance=ed.get("provenance", {}),
            )
        return graph
