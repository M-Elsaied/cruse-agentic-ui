'use client';

import { useMemo, useState, useEffect, useRef } from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import type { AgentTraceEntry } from '@/types/debug';
import type { ConnectivityData, GraphLayout, LayoutNode, LayoutEdge } from '@/types/network';

const NODE_W = 180;
const NODE_H = 56;
const H_GAP = 40;
const V_GAP = 100;
const PADDING = 60;
const ACTIVE_DECAY_MS = 3000;

const TYPE_COLORS: Record<string, string> = {
  llm_agent: '#3b82f6',
  coded_tool: '#22c55e',
  external_agent: '#f97316',
  langchain_tool: '#a855f7',
};

const TYPE_LABELS: Record<string, string> = {
  llm_agent: 'LLM Agent',
  coded_tool: 'Coded Tool',
  external_agent: 'External Agent',
  langchain_tool: 'LangChain Tool',
};

function getColor(displayAs: string): string {
  return TYPE_COLORS[displayAs] || '#6b7280';
}

function computeLayout(data: ConnectivityData): GraphLayout {
  const nodes: LayoutNode[] = [];
  const edges: LayoutEdge[] = [];

  const info = data.connectivity_info;
  if (!info || info.length === 0) {
    return { nodes, edges, width: 0, height: 0 };
  }

  const adjacency = new Map<string, string[]>();
  const displayAsMap = new Map<string, string>();
  const descriptionMap = new Map<string, string>();

  for (const entry of info) {
    adjacency.set(entry.origin, entry.tools || []);
    displayAsMap.set(entry.origin, entry.display_as || 'llm_agent');
    if (entry.metadata?.description) {
      descriptionMap.set(entry.origin, entry.metadata.description);
    }
  }

  const root = info[0].origin;
  const depthMap = new Map<string, number>();
  const queue: string[] = [root];
  depthMap.set(root, 0);

  while (queue.length > 0) {
    const current = queue.shift()!;
    const depth = depthMap.get(current)!;
    const children = adjacency.get(current) || [];
    for (const child of children) {
      if (!depthMap.has(child)) {
        depthMap.set(child, depth + 1);
        queue.push(child);
      }
    }
  }

  for (const entry of info) {
    if (!depthMap.has(entry.origin)) {
      depthMap.set(entry.origin, 0);
    }
  }

  const levelGroups = new Map<number, string[]>();
  for (const [name, depth] of depthMap) {
    if (!levelGroups.has(depth)) {
      levelGroups.set(depth, []);
    }
    levelGroups.get(depth)!.push(name);
  }

  const maxDepth = Math.max(...levelGroups.keys(), 0);
  const maxWidth = Math.max(...[...levelGroups.values()].map((g) => g.length), 1);
  const totalWidth = Math.max(maxWidth * (NODE_W + H_GAP) - H_GAP + PADDING * 2, 400);
  const totalHeight = (maxDepth + 1) * (NODE_H + V_GAP) - V_GAP + PADDING * 2;

  const nodePositions = new Map<string, { x: number; y: number }>();

  for (let depth = 0; depth <= maxDepth; depth++) {
    const group = levelGroups.get(depth) || [];
    const levelWidth = group.length * (NODE_W + H_GAP) - H_GAP;
    const offsetX = (totalWidth - levelWidth) / 2;

    for (let i = 0; i < group.length; i++) {
      const name = group[i];
      const x = offsetX + i * (NODE_W + H_GAP);
      const y = PADDING + depth * (NODE_H + V_GAP);
      nodePositions.set(name, { x, y });

      nodes.push({
        id: name,
        displayAs: displayAsMap.get(name) || 'llm_agent',
        x,
        y,
        width: NODE_W,
        height: NODE_H,
        depth,
        description: descriptionMap.get(name),
      });
    }
  }

  for (const [origin, children] of adjacency) {
    const parentPos = nodePositions.get(origin);
    if (!parentPos) continue;
    for (const child of children) {
      const childPos = nodePositions.get(child);
      if (!childPos) continue;
      edges.push({
        from: origin,
        to: child,
        fromX: parentPos.x + NODE_W / 2,
        fromY: parentPos.y + NODE_H,
        toX: childPos.x + NODE_W / 2,
        toY: childPos.y,
      });
    }
  }

  return { nodes, edges, width: totalWidth, height: totalHeight };
}

function truncateLabel(text: string, maxLen: number = 20): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 1) + '\u2026';
}

/**
 * Resolve an origin segment to a graph node ID.
 * Origin segments come from Origination.get_full_name_from_origin() and may
 * carry an instantiation suffix like "-02". We strip that to match graph IDs.
 */
function resolveNodeId(segment: string, nodeIds: Set<string>): string | null {
  if (nodeIds.has(segment)) return segment;
  // Strip instantiation suffix (e.g. "synonymizer-02" -> "synonymizer")
  const stripped = segment.replace(/-\d+$/, '');
  if (nodeIds.has(stripped)) return stripped;
  return null;
}

/**
 * Parse origin chain into graph node IDs.
 * Origin format from neuro_san is dot-delimited: "announcer.synonymizer"
 * Each segment is a tool name, possibly with an instantiation suffix.
 */
function parseOriginChain(origin: string, nodeIds: Set<string>): string[] {
  if (!origin) return [];
  // Split on "." but preserve "/" in external agent names
  const segments = origin.split('.');
  const resolved: string[] = [];
  for (const seg of segments) {
    const id = resolveNodeId(seg, nodeIds);
    if (id) resolved.push(id);
  }
  return resolved;
}

/** Derive active nodes/edges from recent trace entries */
function useActivityState(traceEntries: AgentTraceEntry[], nodeIds: Set<string>) {
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [activeEdges, setActiveEdges] = useState<Set<string>>(new Set());
  const [recentMessages, setRecentMessages] = useState<AgentTraceEntry[]>([]);
  const lastCountRef = useRef(0);
  const decayTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    if (traceEntries.length === lastCountRef.current) return;

    const newEntries = traceEntries.slice(lastCountRef.current);
    lastCountRef.current = traceEntries.length;

    const batchNodes = new Set<string>();
    const batchEdges = new Set<string>();

    for (const entry of newEntries) {
      // Match agent name directly
      const agent = entry.agent;
      const resolvedAgent = agent ? resolveNodeId(agent, nodeIds) : null;
      if (resolvedAgent) batchNodes.add(resolvedAgent);

      // Parse the dot-delimited origin chain
      const chain = parseOriginChain(entry.origin, nodeIds);
      for (const id of chain) batchNodes.add(id);

      // Consecutive pairs in the chain form edges
      for (let i = 0; i < chain.length - 1; i++) {
        batchEdges.add(`${chain[i]}->${chain[i + 1]}`);
      }
    }

    if (batchNodes.size === 0 && batchEdges.size === 0) {
      setRecentMessages((prev) => [...prev, ...newEntries].slice(-50));
      return;
    }

    setActiveNodes((prev) => {
      const next = new Set(prev);
      batchNodes.forEach((n) => next.add(n));
      return next;
    });
    setActiveEdges((prev) => {
      const next = new Set(prev);
      batchEdges.forEach((e) => next.add(e));
      return next;
    });
    setRecentMessages((prev) => [...prev, ...newEntries].slice(-50));

    // Decay: remove this batch's active state after ACTIVE_DECAY_MS
    const timer = setTimeout(() => {
      setActiveNodes((prev) => {
        const next = new Set(prev);
        batchNodes.forEach((n) => next.delete(n));
        return next;
      });
      setActiveEdges((prev) => {
        const next = new Set(prev);
        batchEdges.forEach((e) => next.delete(e));
        return next;
      });
    }, ACTIVE_DECAY_MS);
    decayTimersRef.current.push(timer);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [traceEntries.length, nodeIds]);

  // Cleanup all timers on unmount
  useEffect(() => {
    return () => {
      decayTimersRef.current.forEach(clearTimeout);
    };
  }, []);

  return { activeNodes, activeEdges, recentMessages };
}

/** Animated dot traveling along a bezier edge */
function TravelingDot({ edge, darkMode }: { edge: LayoutEdge; darkMode: boolean }) {
  const midY = (edge.fromY + edge.toY) / 2;
  const pathD = `M ${edge.fromX} ${edge.fromY} C ${edge.fromX} ${midY}, ${edge.toX} ${midY}, ${edge.toX} ${edge.toY}`;
  const id = `path-${edge.from}-${edge.to}`;

  return (
    <>
      <defs>
        <path id={id} d={pathD} />
      </defs>
      <circle r={4} fill="#3b82f6" opacity={0.9}>
        <animateMotion dur="1.2s" repeatCount="indefinite">
          <mpath href={`#${id}`} />
        </animateMotion>
      </circle>
      <circle r={7} fill="#3b82f6" opacity={0.2}>
        <animateMotion dur="1.2s" repeatCount="indefinite">
          <mpath href={`#${id}`} />
        </animateMotion>
      </circle>
    </>
  );
}

interface NetworkGraphProps {
  data: ConnectivityData;
}

export function NetworkGraph({ data }: NetworkGraphProps) {
  const darkMode = useCruseStore((s) => s.darkMode);
  const traceEntries = useCruseStore((s) => s.debugTraceEntries);
  const isStreaming = useCruseStore((s) => s.isStreaming);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const layout = useMemo(() => computeLayout(data), [data]);

  const nodeIds = useMemo(() => new Set(layout.nodes.map((n) => n.id)), [layout]);

  const { activeNodes, activeEdges, recentMessages } = useActivityState(traceEntries, nodeIds);

  // Auto-scroll the message ticker
  const tickerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (tickerRef.current) {
      tickerRef.current.scrollTop = tickerRef.current.scrollHeight;
    }
  }, [recentMessages.length]);

  if (layout.nodes.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No connectivity data available for this network.
        </Typography>
      </Box>
    );
  }

  const hoveredInfo = layout.nodes.find((n) => n.id === hoveredNode);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Status bar */}
      <Box sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
        <Chip
          size="small"
          label={isStreaming ? 'Live' : 'Idle'}
          color={isStreaming ? 'success' : 'default'}
          variant={isStreaming ? 'filled' : 'outlined'}
          sx={{
            fontSize: '0.7rem',
            height: 22,
            ...(isStreaming && {
              animation: 'pulse 1.5s ease-in-out infinite',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.6 },
              },
            }),
          }}
        />
        <Typography variant="caption" color="text.secondary">
          {layout.nodes.length} agents &middot; {layout.edges.length} connections
          {activeNodes.size > 0 && ` \u00B7 ${activeNodes.size} active`}
        </Typography>
      </Box>

      {/* Graph area */}
      <Box sx={{ flex: 1, overflow: 'auto', position: 'relative', minHeight: 0 }}>
        <svg
          width={Math.max(layout.width, 400)}
          height={layout.height + 60}
          style={{ display: 'block', margin: '0 auto' }}
        >
          {/* Edge lines */}
          {layout.edges.map((edge, i) => {
            const midY = (edge.fromY + edge.toY) / 2;
            const d = `M ${edge.fromX} ${edge.fromY} C ${edge.fromX} ${midY}, ${edge.toX} ${midY}, ${edge.toX} ${edge.toY}`;
            const edgeKey = `${edge.from}->${edge.to}`;
            const isActive = activeEdges.has(edgeKey);
            const isHoverHL = hoveredNode === edge.from || hoveredNode === edge.to;

            return (
              <g key={`edge-${edge.from}-${edge.to}`}>
                <motion.path
                  d={d}
                  fill="none"
                  stroke={
                    isActive
                      ? '#3b82f6'
                      : isHoverHL
                        ? '#64748b'
                        : darkMode
                          ? 'rgba(255,255,255,0.1)'
                          : 'rgba(0,0,0,0.08)'
                  }
                  strokeWidth={isActive ? 2.5 : isHoverHL ? 2 : 1.5}
                  strokeDasharray={isActive ? undefined : undefined}
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: 0.5, delay: i * 0.03 }}
                />
                {/* Active glow */}
                {isActive && (
                  <path
                    d={d}
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth={6}
                    opacity={0.15}
                  />
                )}
              </g>
            );
          })}

          {/* Traveling dots on active edges */}
          {layout.edges.map((edge) => {
            const edgeKey = `${edge.from}->${edge.to}`;
            if (!activeEdges.has(edgeKey)) return null;
            return <TravelingDot key={`dot-${edgeKey}`} edge={edge} darkMode={darkMode} />;
          })}

          {/* Nodes */}
          {layout.nodes.map((node, i) => {
            const color = getColor(node.displayAs);
            const isHovered = hoveredNode === node.id;
            const isActive = activeNodes.has(node.id);

            return (
              <motion.g
                key={node.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'pointer' }}
              >
                {/* Active glow ring */}
                {isActive && (
                  <>
                    <rect
                      x={node.x - 3}
                      y={node.y - 3}
                      width={node.width + 6}
                      height={node.height + 6}
                      rx={10}
                      ry={10}
                      fill="none"
                      stroke={color}
                      strokeWidth={2}
                      opacity={0.5}
                    >
                      <animate
                        attributeName="opacity"
                        values="0.5;0.2;0.5"
                        dur="1.5s"
                        repeatCount="indefinite"
                      />
                    </rect>
                    <rect
                      x={node.x - 6}
                      y={node.y - 6}
                      width={node.width + 12}
                      height={node.height + 12}
                      rx={12}
                      ry={12}
                      fill="none"
                      stroke={color}
                      strokeWidth={1}
                      opacity={0.2}
                    >
                      <animate
                        attributeName="opacity"
                        values="0.2;0.05;0.2"
                        dur="1.5s"
                        repeatCount="indefinite"
                      />
                    </rect>
                  </>
                )}

                {/* Node background */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={node.width}
                  height={node.height}
                  rx={8}
                  ry={8}
                  fill={
                    isActive
                      ? darkMode ? `${color}20` : `${color}12`
                      : darkMode ? 'rgba(15, 23, 42, 0.85)' : 'rgba(255, 255, 255, 0.92)'
                  }
                  stroke={
                    isActive
                      ? color
                      : isHovered
                        ? color
                        : darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'
                  }
                  strokeWidth={isActive ? 2 : isHovered ? 1.5 : 1}
                />
                {/* Color indicator bar */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={4}
                  height={node.height}
                  rx={2}
                  fill={color}
                  opacity={isActive ? 1 : 0.7}
                />
                {/* Active indicator dot */}
                {isActive && (
                  <circle
                    cx={node.x + node.width - 12}
                    cy={node.y + 12}
                    r={4}
                    fill={color}
                  >
                    <animate
                      attributeName="r"
                      values="3;5;3"
                      dur="1s"
                      repeatCount="indefinite"
                    />
                    <animate
                      attributeName="opacity"
                      values="1;0.5;1"
                      dur="1s"
                      repeatCount="indefinite"
                    />
                  </circle>
                )}
                {/* Node label */}
                <text
                  x={node.x + 14}
                  y={node.y + 22}
                  fontSize={12}
                  fontWeight={600}
                  fill={darkMode ? '#e2e8f0' : '#1e293b'}
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {truncateLabel(node.id)}
                </text>
                {/* Type label */}
                <text
                  x={node.x + 14}
                  y={node.y + 40}
                  fontSize={10}
                  fill={isActive ? color : darkMode ? '#64748b' : '#94a3b8'}
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {isActive ? 'Active' : (TYPE_LABELS[node.displayAs] || node.displayAs)}
                </text>
              </motion.g>
            );
          })}

          {/* Legend */}
          {(() => {
            const usedTypes = [...new Set(layout.nodes.map((n) => n.displayAs))];
            const legendY = layout.height + 16;
            const legendItemWidth = 120;
            const legendWidth = usedTypes.length * legendItemWidth;
            const legendX = (layout.width - legendWidth) / 2;

            return (
              <g>
                {usedTypes.map((type, idx) => (
                  <g key={type} transform={`translate(${legendX + idx * legendItemWidth}, ${legendY})`}>
                    <rect width={10} height={10} rx={2} fill={getColor(type)} />
                    <text
                      x={16}
                      y={9}
                      fontSize={10}
                      fill={darkMode ? '#94a3b8' : '#64748b'}
                      fontFamily="Inter, system-ui, sans-serif"
                    >
                      {TYPE_LABELS[type] || type}
                    </text>
                  </g>
                ))}
              </g>
            );
          })()}
        </svg>

        {/* Hover tooltip */}
        {hoveredInfo?.description && (
          <Box
            sx={{
              position: 'absolute',
              bottom: 16,
              left: '50%',
              transform: 'translateX(-50%)',
              px: 2,
              py: 1,
              borderRadius: 1.5,
              bgcolor: darkMode ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              border: '1px solid',
              borderColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
              backdropFilter: 'blur(8px)',
              maxWidth: 400,
              zIndex: 10,
              pointerEvents: 'none',
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 600 }}>
              {hoveredInfo.id}
            </Typography>
            <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.25 }}>
              {hoveredInfo.description}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Live message ticker */}
      <AnimatePresence>
        {recentMessages.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ flexShrink: 0, overflow: 'hidden' }}
          >
            <Box
              sx={{
                borderTop: '1px solid',
                borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
                maxHeight: 160,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Box sx={{ px: 2, py: 0.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                  Agent Messages
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({recentMessages.length})
                </Typography>
              </Box>
              <Box
                ref={tickerRef}
                sx={{
                  overflow: 'auto',
                  px: 2,
                  pb: 1,
                  flex: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.7rem',
                  lineHeight: 1.6,
                }}
              >
                {recentMessages.slice(-20).map((msg) => (
                  <Box key={msg.id} sx={{ display: 'flex', gap: 1, opacity: 0.85 }}>
                    <Typography
                      component="span"
                      sx={{
                        fontSize: 'inherit',
                        fontFamily: 'inherit',
                        fontWeight: 700,
                        color: nodeIds.has(msg.agent)
                          ? getColor(layout.nodes.find((n) => n.id === msg.agent)?.displayAs || '')
                          : 'text.secondary',
                        whiteSpace: 'nowrap',
                        minWidth: 100,
                      }}
                    >
                      {msg.agent || '?'}
                    </Typography>
                    <Typography
                      component="span"
                      sx={{
                        fontSize: 'inherit',
                        fontFamily: 'inherit',
                        color: 'text.secondary',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {msg.text.slice(0, 120)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
}
