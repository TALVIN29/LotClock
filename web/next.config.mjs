/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",          // fully static -> deploys on Vercel/Netlify with no backend
  images: { unoptimized: true },
};
export default nextConfig;
