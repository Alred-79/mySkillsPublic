// HTTP fetching for the web side. Real call-sites for the `request` dependency,
// so a replacement recommendation has something concrete to be grounded on (gate 4).
//
// `request` is deprecated (npm-deprecated since 2020). These three call-sites are
// what a migration would touch; the migration-cost gate (gate 5) should count them.

const request = require("request");

function getUser(id, cb) {
  request.get(
    { url: `https://api.example.com/users/${id}`, json: true },
    (err, res, body) => {
      if (err) return cb(err);
      cb(null, body);
    }
  );
}

function listOrders(userId, cb) {
  request.get(
    { url: `https://api.example.com/users/${userId}/orders`, json: true },
    (err, res, body) => {
      if (err) return cb(err);
      cb(null, body);
    }
  );
}

function postEvent(event, cb) {
  request.post(
    { url: "https://api.example.com/events", json: event },
    (err, res, body) => {
      if (err) return cb(err);
      cb(null, body);
    }
  );
}

module.exports = { getUser, listOrders, postEvent };
