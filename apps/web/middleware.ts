import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks/clerk",
]);

export default clerkMiddleware((auth, request) => {
  if (isPublicRoute(request)) {
    return;
  }
});

export const config = {
  matcher: [
    "/((?!.*|.*\\..*|_next).*)",
    "/",
    "/(api|trpc)(.*)",
  ],
};