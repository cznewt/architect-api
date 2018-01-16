d3.hive = {};
d3.hive.link = function() {
  var source = function(d) { return d.source; },
      target = function(d) { return d.target; },
      angle = function(d) { return d.angle; },
      startRadius = function(d) { return d.radius; },
      endRadius = startRadius,
      arcOffset = 0;

  function link(d, i) {
    var s = node(source, this, d, i),
        t = node(target, this, d, i),
        x;
    if (t.a < s.a) x = t, t = s, s = x;
    if (t.a - s.a > Math.PI) s.a += 2 * Math.PI;
    var a1 = s.a + (t.a - s.a) / 3,
        a2 = t.a - (t.a - s.a) / 3;
    return s.r0 - s.r1 || t.r0 - t.r1
        ? "M" + Math.cos(s.a) * s.r0 + "," + Math.sin(s.a) * s.r0
        + "L" + Math.cos(s.a) * s.r1 + "," + Math.sin(s.a) * s.r1
        + "C" + Math.cos(a1) * s.r1 + "," + Math.sin(a1) * s.r1
        + " " + Math.cos(a2) * t.r1 + "," + Math.sin(a2) * t.r1
        + " " + Math.cos(t.a) * t.r1 + "," + Math.sin(t.a) * t.r1
        + "L" + Math.cos(t.a) * t.r0 + "," + Math.sin(t.a) * t.r0
        + "C" + Math.cos(a2) * t.r0 + "," + Math.sin(a2) * t.r0
        + " " + Math.cos(a1) * s.r0 + "," + Math.sin(a1) * s.r0
        + " " + Math.cos(s.a) * s.r0 + "," + Math.sin(s.a) * s.r0
        : "M" + Math.cos(s.a) * s.r0 + "," + Math.sin(s.a) * s.r0
        + "C" + Math.cos(a1) * s.r1 + "," + Math.sin(a1) * s.r1
        + " " + Math.cos(a2) * t.r1 + "," + Math.sin(a2) * t.r1
        + " " + Math.cos(t.a) * t.r1 + "," + Math.sin(t.a) * t.r1;
  }

  function node(method, thiz, d, i) {
    var node = method.call(thiz, d, i),
        a = +(typeof angle === "function" ? angle.call(thiz, node, i) : angle) + arcOffset,
        r0 = +(typeof startRadius === "function" ? startRadius.call(thiz, node, i) : startRadius),
        r1 = (startRadius === endRadius ? r0 : +(typeof endRadius === "function" ? endRadius.call(thiz, node, i) : endRadius));
    return {r0: r0, r1: r1, a: a};
  }

  link.source = function(_) {
    if (!arguments.length) return source;
    source = _;
    return link;
  };

  link.target = function(_) {
    if (!arguments.length) return target;
    target = _;
    return link;
  };

  link.angle = function(_) {
    if (!arguments.length) return angle;
    angle = _;
    return link;
  };

  link.radius = function(_) {
    if (!arguments.length) return startRadius;
    startRadius = endRadius = _;
    return link;
  };

  link.startRadius = function(_) {
    if (!arguments.length) return startRadius;
    startRadius = _;
    return link;
  };

  link.endRadius = function(_) {
    if (!arguments.length) return endRadius;
    endRadius = _;
    return link;
  };

  return link;
};

String.prototype.formatTemplate = String.prototype.formatTemplate ||
function () {
    "use strict";
    var str = this.toString();
    if (arguments.length) {
        var t = typeof arguments[0];
        var key;
        var args = ("string" === t || "number" === t) ?
            Array.prototype.slice.call(arguments)
            : arguments[0];

        for (key in args) {
            str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
        }
    }

    return str;
};

Math.radians = function(degrees) {
  return degrees * Math.PI / 180;
};

Math.degrees = function(radians) {
  return radians * 180 / Math.PI;
};

var iconMapping = {};

var iconFunctions = {
    family: function(d) {
       return iconMapping[d].family;
    },
    color: function(d) {
        return iconMapping[d].color;
    },
    character: function(d) {
        return String.fromCharCode(iconMapping[d].char);
    },
    size: function(d) {
        return iconMapping[d].size + 'px';
    },
    transform: function(d) {
        return 'translate('+ iconMapping[d].x + ', ' + iconMapping[d].y + ')';
    }
};

var relationalPlotHelpers = {

  displayResources: function(resources) {
      $("#plotResources").html(resources);
  },

  displayRelations: function(relations) {
      $("#plotRelations").html(relations);
  },

  displayScrapeTime: function(date) {
      $("#plotScrapeTime time").remove();
      $("#plotScrapeTime").html("<time datetime='"+date+"''>N/A</time>");
      $("#plotScrapeTime time").timeago();
  },

  nodeRelations: function(nodes) {
    var map = {},
        relations = [];

    // Compute a map from name to node.
    nodes.forEach(function(d) {
      map[d.data.name] = d;
    });

    // For each import, construct a link from the source to target node.
    nodes.forEach(function(d) {
      if (d.data.relations) d.data.relations.forEach(function(i) {
        relations.push(map[d.data.name].path(map[i]));
      });
    });

    return relations;
  },

  nodeHierarchy: function(nodes) {
    var map = {};

    function find(name, data) {
      var node = map[name], i;
      if (!node) {
        node = map[name] = data || {name: name, children: []};
        if (name.length) {
          node.parent = find(name.substring(0, i = name.lastIndexOf("|")));
          node.parent.children.push(node);
          node.key = name.substring(i + 1);
        }
      }
      return node;
    }

    nodes.forEach(function(d) {
      find(d.name, d);
    });

    return d3.hierarchy(map[""]);
  },

  nodeServiceId: function(d){
    if(d && d.host && d.service){
        return "node-" + d.host.replace(/\./g,"_") + "-service-" + d.service.replace(/\./g,"_");
    }else{
        console.log("Cannot generate node-service ID, given node or its host/service is undefined! node: " + relationalPlotHelpers.nodeToString(d));
        return "node-" + (node.host?node.host:"UNDEFINED_HOST") + (node.service?node.service:"UNDEFINED_SERVICE");
    }
  },

  nodeToString: function(n, hideRelations){
       var cleanNode = {};
       $.extend(cleanNode, n);
       delete cleanNode.children;
       delete cleanNode.parent;
       if(hideRelations){
         delete cleanNode.relations;
       }
       return JSON.stringify(cleanNode);
  },
  root: function(classes) {
    var map = {};
    var parentObj = {host:"", children:[]};
    var addedHosts = []

    classes.forEach(function(d) {
      //create hosts array
       if(addedHosts.indexOf(d.host) === -1){
          addedHosts.push(d.host);
          var newHost={host: d.host, service: d.host, parent: parentObj}
          newHost.children = [$.extend({parent:newHost}, d)]
          parentObj.children.push(newHost);
      }else{
          // find host and add children
          parentObj.children.forEach(function(item){
            if(item.host == d.host){
                item.children.push($.extend({parent:item}, d))
            }
          });
      }
    });

    return parentObj;
  },

  // Return a list of imports for the given array of nodes.
  imports: function(nodes) {
    var map = {},
        imports = [];

    // Compute a map from name to node.
    nodes.forEach(function(d) {
      map[d.host+"_"+d.service] = d;
    });

    // For each import, construct a link from the source to target node.
    nodes.forEach(function(d) {
      if (d.relations) {
        d.relations.forEach(function(i) {
            var line = {source: map[d.host+"_"+d.service], target: map[i.host + "_" + i.service], link_str: 2};
            if(line.source && line.target){
                imports.push(line);
            }else{
                console.log("Cannot create relation link, node: " + relationalPlotHelpers.nodeToString(d) + " relation: " + JSON.stringify(i));
            }
        });
      }
    });
    return imports;
  }
};
