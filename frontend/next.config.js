/** @type {import('next').NextConfig} */
const { i18n } = require('./next-i18next.config');

const nextConfig = {
  // Keep dev output separate from production builds so `next build`
  // doesn't corrupt the files a running `next dev` server expects.
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  reactStrictMode: true,
  i18n,
};

module.exports = nextConfig;
