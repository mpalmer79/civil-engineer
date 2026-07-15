/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      // Canonical proof-of-concept route with permanent redirects from the
      // short and unhyphenated forms.
      {
        source: "/proofofconcept",
        destination: "/proof-of-concept",
        permanent: true,
      },
      {
        source: "/poc",
        destination: "/proof-of-concept",
        permanent: true,
      },
      // The standalone landing page consolidated into the homepage. The
      // route stays as a redirect so bookmarked links keep working.
      {
        source: "/landing",
        destination: "/",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
