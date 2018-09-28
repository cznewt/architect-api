var RelationalPlot = function (RelationalPlot) {
    /**
     * Circle pack rendering method
     *
     * Adapted from https://bl.ocks.org/Kallirroi/a66f7f8a5e8ae56ba1032687c783b8ab
     *
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.circlePack = function (dataUrl, graphSelector, refreshInterval) {

        var color = d3.scaleLinear()
            .domain([-1, 5])
            .range(["hsl(15,80%,77%)", "hsl(228,30%,40%)"])
            .interpolate(d3.interpolateHcl),
            margin = 0,
            diameter,
            pack,
            graph = this;
        this._data = {};

        this.init = function (alreadyRunning) {
            diameter = Math.min(
                $(graphSelector).innerWidth(),
                $(graphSelector).innerHeight()
            );
            pack = d3.pack()
                .size([diameter - margin, diameter - margin])
                .padding(margin / 2);
            if (alreadyRunning && graph.svg) {
                graph.svg.remove();
            }

            graph.svg = d3.select(graphSelector).append("svg")
                .attr("width", diameter)
                .attr("height", diameter);
            g = graph.svg.append("g").attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

            if (!alreadyRunning) {
                graph.requestData(dataUrl, graph.render);
                $(window).on('resize', function (ev) {
                    graph.init(true);
                    graph.render();
                });

                if (refreshInterval) {
                    setInterval(function () {
                        graph.requestData(dataUrl, function () {
                            graph.init(true);
                            graph.render();
                        });
                    }, refreshInterval * 1000);
                }
            }
        };

        this.render = function () {

            root = d3.hierarchy(graph._data)
                .sum(function (d) { return d.size; })
                .sort(function (a, b) { return b.value - a.value; });

            var focus = root,
                nodes = pack(root).descendants(),
                view;

            var circle = g.selectAll("circle")
                .data(nodes)
                .enter().append("circle")
                .attr("class", function (d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
                .style("fill", function (d) { return d.children ? color(d.depth) : null; })
                .on("click", function (d) { if (focus !== d) zoom(d), d3.event.stopPropagation(); });

            var text = g.selectAll("text")
                .data(nodes)
                .enter().append("text")
                .attr("class", "label")
                .style("fill-opacity", function (d) { return d.parent === root ? 1 : 0; })
                .style("display", function (d) { return d.parent === root ? "inline" : "none"; })
                .text(function (d) { return d.data.name; });

            var node = g.selectAll("circle,text");

            graph.svg
                .on("click", function () { zoom(root); });

            zoomTo([root.x, root.y, root.r * 2 + margin]);

            function zoom(d) {
                var focus0 = focus; focus = d;

                var transition = d3.transition()
                    .duration(d3.event.altKey ? 7500 : 750)
                    .tween("zoom", function (d) {
                        var i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2 + margin]);
                        return function (t) { zoomTo(i(t)); };
                    });

                transition.selectAll("text")
                    .filter(function (d) { return d.parent === focus || this.style.display === "inline"; })
                    .style("fill-opacity", function (d) { return d.parent === focus ? 1 : 0; })
                    .on("start", function (d) { if (d.parent === focus) this.style.display = "inline"; })
                    .on("end", function (d) { if (d.parent !== focus) this.style.display = "none"; });
            }

            function zoomTo(v) {
                var k = diameter / v[2]; view = v;
                node.attr("transform", function (d) { return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")"; });
                circle.attr("r", function (d) { return d.r * k; });
            }

        };

        this.requestData = function (dataUrl, callback) {
            d3.json(dataUrl, function (res) {
                console.log(res);
                graph._data = res.resources;
                if (typeof callback === 'function') {
                    callback();
                }
            });
        };

    };
    return RelationalPlot;
}(RelationalPlot || {});
