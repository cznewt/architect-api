var RelationalPlot = function(RelationalPlot){
    /**
     * Tree map rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.treeMap = function(dataUrl, graphSelector, refreshInterval){

      var width = $(graphSelector).innerWidth(),
          height = width * 2/3;

      var format = d3.format(",d");

      var color = d3.scaleOrdinal()
          .range(d3.schemeCategory10
              .map(function(c) { c = d3.rgb(c); c.opacity = 0.6; return c; }));

      var stratify = d3.stratify()
          .parentId(function(d) { return d.id.substring(0, d.id.lastIndexOf(".")); });

      var graph = this;
      this._data = {};

      this.init = function(alreadyRunning){
          if(alreadyRunning && graph.treemap){
             graph.treemap.remove();
          }

          graph.treemap = d3.treemap()
              .size([width, height])
              .padding(1)
              .round(true);

        if(!alreadyRunning){
            graph.requestData(dataUrl, graph.render);
            $(window).on('resize', function(ev){
                graph.resetPosition();
                graph.init(true);
                graph.render();
            });

            if(refreshInterval){
                setInterval(function(){
                    graph.requestData(dataUrl, function(){
                        graph.init(true);
                        graph.render();
                    });
                }, refreshInterval * 1000);
            }
        }
      };
      this.render = function(){

          var root = stratify(graph._data)
              .sum(function(d) { return d.value; })
              .sort(function(a, b) { return b.height - a.height || b.value - a.value; });

          graph.treemap(root);

          d3.select(selector)
            .selectAll(".node")
            .data(root.leaves())
            .enter().append("div")
              .attr("class", "node")
              .attr("title", function(d) { return d.id + "\n" + format(d.value); })
              .style("left", function(d) { return d.x0 + "px"; })
              .style("top", function(d) { return d.y0 + "px"; })
              .style("width", function(d) { return d.x1 - d.x0 + "px"; })
              .style("height", function(d) { return d.y1 - d.y0 + "px"; })
              .style("background", function(d) { while (d.depth > 1) d = d.parent; return color(d.id); })
            .append("div")
              .attr("class", "node-label")
              .text(function(d) { return d.id.substring(d.id.lastIndexOf(".") + 1).split(/(?=[A-Z][^A-Z])/g).join("\n"); })
            .append("div")
              .attr("class", "node-value")
              .text(function(d) { return format(d.value); });

      };
        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                if(res && res.result === 'ok'){
                    graph._data = res.data;
                    console.log(graph._data)
                    if(typeof callback === 'function'){
                        callback();
                    }
                }else{
                    console.log("Cannot create topology graph, server returns error: " + res.data);
                }
            });
        };
    };
    return RelationalPlot;
}(RelationalPlot || {});