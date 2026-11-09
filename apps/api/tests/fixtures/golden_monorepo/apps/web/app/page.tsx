import React from "react";
import { AppHeader } from "../components/AppHeader";
import { UserCard } from "../components/UserCard";
import { useUserSession } from "../hooks/useUserSession";

export default function HomePage() {
  const { user, loading } = useUserSession();

  if (loading) {
    return <div>Loading session...</div>;
  }

  return (
    <main>
      <AppHeader title="CodeAtlas Dashboard" unreadCount={3} />
      {user && <UserCard user={user} />}
    </main>
  );
}

