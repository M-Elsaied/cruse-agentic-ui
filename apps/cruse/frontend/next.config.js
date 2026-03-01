/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  transpilePackages: ['@mui/material', '@mui/icons-material', '@rjsf/core', '@rjsf/mui'],
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'img.clerk.com' },
    ],
  },
};

module.exports = nextConfig;
