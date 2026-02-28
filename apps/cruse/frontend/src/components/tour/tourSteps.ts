export type TourPlacement = 'top' | 'bottom' | 'left' | 'right' | 'center';

export interface TourStep {
  /** data-tour attribute value on the target element, or null for centered steps */
  target: string | null;
  title: string;
  description: string;
  placement: TourPlacement;
}

export const tourSteps: TourStep[] = [
  {
    target: null,
    title: 'Welcome to CRUSE',
    description:
      'CRUSE is your interactive playground for multi-agent AI networks. ' +
      "Let's take a quick tour of the key components.",
    placement: 'center',
  },
  {
    target: 'network-selector',
    title: 'Agent Network Selector',
    description:
      'Choose from available agent networks here. Each network is a pre-configured team of AI agents that collaborate to solve tasks.',
    placement: 'bottom',
  },
  {
    target: 'chat-panel',
    title: 'Chat Area',
    description:
      'This is where your conversation with the agent network appears. Messages stream in real-time as agents collaborate on your request.',
    placement: 'left',
  },
  {
    target: 'input-bar',
    title: 'Message Input',
    description:
      'Type your messages here and press Enter or click Send. When a form widget is active, your form data is sent along with your message.',
    placement: 'top',
  },
  {
    target: 'widget-area',
    title: 'Dynamic Widget Panel',
    description:
      'Interactive forms and widgets appear here when agents need structured input from you — sliders, file uploads, ratings, and more.',
    placement: 'right',
  },
  {
    target: 'debug-toggle',
    title: 'Debug Monitor',
    description:
      'Toggle the debug panel to inspect agent traces, view server logs, and understand how agents communicate behind the scenes.',
    placement: 'bottom',
  },
  {
    target: 'theme-toggle',
    title: 'Theme Toggle',
    description:
      'Switch between dark and light mode. Each agent network can also bring its own dynamic background theme.',
    placement: 'bottom',
  },
  {
    target: null,
    title: "You're All Set!",
    description:
      'Start by selecting an agent network from the dropdown. Try asking a question and watch the agents collaborate in real-time!',
    placement: 'center',
  },
];
