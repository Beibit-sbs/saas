export interface LocalUser {
  user_id: string;
  login: string;
  display_name: string;
  roles: string[];
  default_language: string;
  created_at?: string;
}

export interface LocalUsersResponse {
  users: LocalUser[];
}

export interface CreateLocalUserPayload {
  login: string;
  password: string;
  display_name: string;
  roles: string[];
  default_language: string;
}

export interface UpdateLocalUserPayload {
  display_name?: string;
  language?: string;
  roles?: string[];
}

export interface SetPasswordPayload {
  password: string;
}
