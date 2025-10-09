/* global requirejs */

requirejs.config({
  shim: {
    jquery: {
      exports: '$'
    },
    cookie: {
      exports: 'Cookies'
    },
    bootstrap: {
      deps: ['jquery']
    }
  },
  baseUrl: '/static/simple_dashboard/js/app',
  paths: {
    app: '/static/simple_dashboard/js/app',
    bootstrap: '/static/simple_dashboard/js/vendor/bootstrap.bundle.min',
    jquery: '/static/simple_dashboard/js/vendor/jquery-3.4.0.min',
    cookie: '/static/simple_dashboard/js/vendor/js.cookie'
  }
})

requirejs(['cookie', 'bootstrap', 'jquery'], function (Cookies, bootstrap) {
  const csrftoken = Cookies.get('csrftoken')

  function csrfSafeMethod (method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method))
  }

  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken)
      }
    }
  })
})
