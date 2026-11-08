export interface UserDTO {
  id: string;
  email: string;
  name: string;
  isActive: boolean;
  createdAt: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
}

export type UserRole = "admin" | "member" | "viewer";

