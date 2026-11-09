import React from "react";
import type { UserDTO } from "@repo/common";
import { formatUserName } from "@repo/common";

export interface UserCardProps {
  user: UserDTO;
  onSelect?: (id: string) => void;
}

export const UserCard = ({ user, onSelect }: UserCardProps) => {
  const displayName = formatUserName(user.name);
  return (
    <div className="user-card" onClick={() => onSelect?.(user.id)}>
      <h3>{displayName}</h3>
      <p>{user.email}</p>
    </div>
  );
};

