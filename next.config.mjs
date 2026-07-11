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
    ];
  },
};

export default nextConfig;
