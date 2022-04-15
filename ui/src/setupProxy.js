const createProxyMiddleware = require('http-proxy-middleware')

module.exports = function (app) {
  app.use(
    createProxyMiddleware('/eaws_api', {
      target: 'http://localhost:1026',
      changeOrigin: true,
      pathRewrite: { '^/eaws_api': '/' }
    })
  )
}
