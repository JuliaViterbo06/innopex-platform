/* =====================================================================
   InnOpEx — cliente da API.
   Todas as telas falam com o back-end Python SOMENTE por aqui.
   ===================================================================== */
var Api = (function () {
  function request(method, url, body) {
    var opts = { method: method, credentials: "same-origin", headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (res) {
      return res.text().then(function (txt) {
        var data = null;
        try { data = txt ? JSON.parse(txt) : null; } catch (e) { data = txt; }
        if (!res.ok) {
          var msg = (data && data.detail) || ("Erro " + res.status);
          if (Array.isArray(msg)) msg = msg.map(function (d) { return d.msg; }).join(" · ");
          var err = new Error(msg); err.status = res.status; throw err;
        }
        return data;
      });
    });
  }
  return {
    meta: function () { return request("GET", "/api/meta"); },
    me: function () { return request("GET", "/api/me"); },
    devLogin: function (d) { return request("POST", "/api/auth/dev-login", d); },
    logout: function () { return request("POST", "/api/auth/logout"); },

    projects: function () { return request("GET", "/api/projects"); },
    createProject: function (d) { return request("POST", "/api/projects", d); },
    updateProject: function (id, d) { return request("PUT", "/api/projects/" + encodeURIComponent(id), d); },
    movePhase: function (id, phase) { return request("POST", "/api/projects/" + encodeURIComponent(id) + "/phase", { phase: phase }); },

    schedule: function () { return request("GET", "/api/schedule"); },
    agenda: function (day) { return request("GET", "/api/schedule/" + day + "/agenda"); },
    notes: function (id, d) { return request("POST", "/api/projects/" + encodeURIComponent(id) + "/notes", d); },
    accept: function (id) { return request("POST", "/api/projects/" + encodeURIComponent(id) + "/meeting/accept"); },
    decline: function (id) { return request("POST", "/api/projects/" + encodeURIComponent(id) + "/meeting/decline"); },

    decks: function () { return request("GET", "/api/decks"); },
    uploadDeck: function (d) { return request("POST", "/api/decks", d); },

    notifications: function () { return request("GET", "/api/notifications"); },
    readAll: function () { return request("POST", "/api/notifications/read-all"); },
    readOne: function (id) { return request("POST", "/api/notifications/" + encodeURIComponent(id) + "/read"); },

    config: function () { return request("GET", "/api/config"); },
    saveConfig: function (d) { return request("PUT", "/api/config", d); },
    users: function () { return request("GET", "/api/admin/users"); },
    pending: function () { return request("GET", "/api/admin/pending-decisions"); },
    reset: function () { return request("POST", "/api/admin/reset"); },

    dashboard: function () { return request("GET", "/api/dashboard"); },
    nopex: function (q) { return request("POST", "/api/nopex", { question: q }); }
  };
})();
