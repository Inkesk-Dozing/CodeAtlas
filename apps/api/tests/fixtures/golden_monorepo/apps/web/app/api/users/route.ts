import { NextResponse } from "next/server";
import type { UserDTO } from "@repo/common";

export async function GET(request: Request) {
  const users: UserDTO[] = [
    {
      id: "u_1",
      name: "Ada Lovelace",
      email: "ada@example.com",
      isActive: true,
      createdAt: "2026-01-01T00:00:00Z",
    },
  ];
  return NextResponse.json({ data: users, success: true });
}

export async function POST(request: Request) {
  const body = await request.json();
  return NextResponse.json({ data: body, success: true }, { status: 201 });
}

