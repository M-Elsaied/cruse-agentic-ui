/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  transpilePackages: ['@mui/material', '@mui/icons-material', '@rjsf/core', '@rjsf/mui'],
};

module.exports = nextConfig;
