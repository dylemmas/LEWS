import { create } from 'zustand';
import type { NodeDTO, NodeStatus } from '@lews/shared-types';

interface NodesState {
  nodeStatus: Map<string, NodeStatus>;
  nodeBattery: Map<string, number | null>;
  setNodeStatus(nodeId: string, status: NodeStatus): void;
  setNodeBattery(nodeId: string, mv: number | null): void;
}

export const useNodesStore = create<NodesState>((set) => ({
  nodeStatus: new Map(),
  nodeBattery: new Map(),
  setNodeStatus: (nodeId, status) =>
    set((state) => {
      const next = new Map(state.nodeStatus);
      next.set(nodeId, status);
      return { nodeStatus: next };
    }),
  setNodeBattery: (nodeId, mv) =>
    set((state) => {
      const next = new Map(state.nodeBattery);
      next.set(nodeId, mv);
      return { nodeBattery: next };
    }),
}));
