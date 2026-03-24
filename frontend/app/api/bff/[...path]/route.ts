import { NextRequest } from "next/server";
import { proxyBffRequest } from "@/shared/server/bff-proxy";

type Ctx = { params: { path: string[] } };

export async function GET(request: NextRequest, context: Ctx) {
  return proxyBffRequest(request, context.params.path);
}

export async function POST(request: NextRequest, context: Ctx) {
  return proxyBffRequest(request, context.params.path);
}

export async function PUT(request: NextRequest, context: Ctx) {
  return proxyBffRequest(request, context.params.path);
}

export async function PATCH(request: NextRequest, context: Ctx) {
  return proxyBffRequest(request, context.params.path);
}

export async function DELETE(request: NextRequest, context: Ctx) {
  return proxyBffRequest(request, context.params.path);
}
