/**
 * Legacy /admin overlays are disabled because middleware redirects the route to
 * the canonical /console/platform entrypoint before page render.
 */
export default function RootLayoutOverlays() {
  return null;
}
