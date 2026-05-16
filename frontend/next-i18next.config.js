module.exports = {
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'hi'],
  },
  localePath: typeof window === 'undefined' ? require('path').resolve('./locales') : './locales',
};