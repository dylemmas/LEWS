import { create } from 'zustand';
import type { ReadingDTO, ReadingEvent } from '@lews/shared-types';

interface ReadingsState {
  latestReading: Map<string, ReadingDTO>;
  updateReading(nodeId: string, reading: ReadingDTO | ReadingEvent): void;
}

export const useReadingsStore = create<ReadingsState>((set) => ({
  latestReading: new Map(),
  updateReading: (nodeId, reading) =>
    set((state) => {
      const next = new Map(state.latestReading);
      next.set(nodeId, reading as ReadingDTO);
      return { latestReading: next };
    }),
}));
