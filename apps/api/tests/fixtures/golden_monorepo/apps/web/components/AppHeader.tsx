import React from "react";

export interface HeaderProps {
  title: string;
  unreadCount?: number;
}

export const AppHeader = ({ title, unreadCount = 0 }: HeaderProps) => {
  return (
    <header className="app-header">
      <h1>{title}</h1>
      {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
    </header>
  );
};

