import { NextRequest, NextResponse } from "next/server";
import { Webhook } from "svix";
import { CLERK_WEBHOOK_SECRET } from "@/lib/env";

export async function POST(req: NextRequest) {
  if (!CLERK_WEBHOOK_SECRET) {
    return NextResponse.json(
      { error: "Webhook secret not configured" },
      { status: 500 }
    );
  }

  const payload = await req.text();
  const headersObj: Record<string, string> = {};
  req.headers.forEach((value, key) => {
    headersObj[key] = value;
  });

  const wh = new Webhook(CLERK_WEBHOOK_SECRET);
  let msg;
  try {
    msg = wh.verify(payload, headersObj);
  } catch (err) {
    return NextResponse.json(
      { error: "Invalid signature" },
      { status: 401 }
    );
  }

  // Forward to backend
  const backendResponse = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/webhooks/clerk`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(msg),
    }
  );

  if (!backendResponse.ok) {
    return NextResponse.json(
      { error: "Failed to sync user" },
      { status: 500 }
    );
  }

  return NextResponse.json({ status: "ok" });
}