var CompositePlot = function (CompositePlot) {
    /**
     * Comoposite chart rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    CompositePlot.chart = function (dataUrl, graphSelector, refreshInterval) {

        var graph = this;
        this._data = null;

        var width, height;

        this.init = function (alreadyRunning) {
            if (alreadyRunning && graph.svg) {
                graph.chart.remove()
            }
            width = $(graphSelector).innerWidth();
            height = $(graphSelector).innerHeight();

            if (!alreadyRunning) {
                graph.requestData(dataUrl, graph.render);
                graph.render();

                $(window).on('resize', function (ev) {
                    graph.init(true);
                    graph.render();
                });
                if (refreshInterval) {
                    setInterval(function () {
                        graph.init(true);
                        graph.render();
                    }, refreshInterval * 1000000);
                }
            }
        };

        this.render = function () {
            console.log(graphSelector);
//            d3.select(graphSelector).node().appendChild(graph._data);
            svg = d3.select(graphSelector+ ' svg')

            svg.append("rect")
                .attr("width", width)
                .attr("height", height)
                .style("fill", "none")
                .style("pointer-events", "all")
                .call(d3.zoom()
                    .scaleExtent([1 / 2, 4])
                    .on("zoom", this.zoomed));

        };

        this.zoomed = function() {
            var transform = d3.event.transform;
            circle.attr("transform", function (d) {
                return "translate(" + transform.applyX(d[0]) + "," + transform.applyY(d[1]) + ")";
            });
        }


        this.requestData = function (dataUrl, callback) {
            d3.xml(dataUrl).mimeType("image/svg+xml").get(function (error, xml) {
                if (error) throw error;
//                graph._data = xml.documentElement;
                d3.select(graphSelector).node().appendChild(xml.documentElement);
                if (typeof callback === 'function') {
                    callback();
                }
            });

        };

    };
    return CompositePlot;
}(CompositePlot || {});
