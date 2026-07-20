// Uses underscore for the same class of job util.js uses lodash for. Having both
// lodash AND underscore in one app is the overlapping-deps case: they are
// near-substitutes, and the repo would benefit from consolidating onto one.

const _ = require("underscore");

function summarize(rows) {
  const byUser = _.groupBy(rows, "userId");
  return _.map(byUser, (items, userId) => ({
    userId,
    total: _.reduce(items, (sum, r) => sum + Number(r.amount), 0),
  }));
}

module.exports = { summarize };
