// Utility helpers. Both lodash and underscore are imported across the codebase
// (this file uses lodash; summarize.js uses underscore) for overlapping jobs -
// map, groupBy, uniq. That overlap is the consolidation opportunity (gate 3/4):
// keep one utility library, not two.

const _ = require("lodash");

function topCategories(rows) {
  const grouped = _.groupBy(rows, "category");
  return _.map(grouped, (items, category) => ({
    category,
    count: items.length,
  }));
}

function uniqueUsers(rows) {
  return _.uniq(_.map(rows, "userId"));
}

module.exports = { topCategories, uniqueUsers };
