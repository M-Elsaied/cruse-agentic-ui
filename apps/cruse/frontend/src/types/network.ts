export interface ConnectivityNode {
  origin: string;
  tools: string[];
  display_as: string;
  metadata?: { description?: string; [key: string]: unknown };
}

export interface ConnectivityData {
  connectivity_info: ConnectivityNode[];
  metadata?: { description?: string; tags?: string[]; [key: string]: unknown };
}

export interface LayoutNode {
  id: string;
  displayAs: string;
  x: number;
  y: number;
  width: number;
  height: number;
  depth: number;
  description?: string;
}

export interface LayoutEdge {
  from: string;
  to: string;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

export interface GraphLayout {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  width: number;
  height: number;
}
