import { useEffect, useState } from "react";
import type { UserDTO } from "@repo/common";

export interface SessionState {
  user: UserDTO | null;
  loading: boolean;
}

export function useUserSession() {
  const [session, setSession] = useState<SessionState>({ user: null, loading: true });

  useEffect(() => {
    fetch("/api/users")
      .then((res) => res.json())
      .then((data) => setSession({ user: data, loading: false }))
      .catch(() => setSession({ user: null, loading: false }));
  }, []);

  return session;
}

