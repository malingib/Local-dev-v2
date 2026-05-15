import { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface VisualSwarmGraphProps {
  agents: any[];
  activity: any[];
}

export function VisualSwarmGraph({ agents, activity }: VisualSwarmGraphProps) {
  // Create nodes for agents
  const initialNodes: Node[] = agents.map((agent, i) => ({
    id: agent.id,
    data: { label: agent.name },
    position: { x: 250 + 200 * Math.cos(2 * Math.PI * i / agents.length), y: 250 + 200 * Math.sin(2 * Math.PI * i / agents.length) },
    style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '8px', padding: '10px', fontSize: '12px' },
  }));

  // Create edges based on activity (simplified: show recent interactions)
  const initialEdges: Edge[] = [];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="h-[500px] w-full border border-slate-800 rounded-lg overflow-hidden bg-slate-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Controls />
        <MiniMap nodeColor="#3b82f6" maskColor="rgba(0,0,0,0.5)" />
        <Background color="#334155" gap={20} />
      </ReactFlow>
    </div>
  );
}
