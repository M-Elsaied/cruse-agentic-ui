export interface NetworkInfo {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  is_shared: boolean;
  network_path: string;
  created_at: string;
  updated_at: string;
}

export interface NetworkDetail extends NetworkInfo {
  hocon_content: string;
}

export interface NetworkListResponse {
  my_networks: NetworkInfo[];
  shared_networks: NetworkInfo[];
}

export interface CustomNetworksSummary {
  my_networks: { name: string; slug: string; network_path: string }[];
  shared_networks: { name: string; slug: string; network_path: string }[];
}
