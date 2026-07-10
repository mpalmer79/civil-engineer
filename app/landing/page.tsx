import { redirect } from "next/navigation";

// The standalone landing page consolidated into the homepage. The route stays
// as a redirect so bookmarked links keep working.
export default function LandingRedirect() {
  redirect("/");
}
