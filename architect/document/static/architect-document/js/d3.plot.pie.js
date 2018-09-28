var QuantitativePlot = function (QuantitativePlot) {
    /**
     * Pie chart rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    QuantitativePlot.pieChart = function (dataUrl, graphSelector, refreshInterval) {

        var graph = this;
        this._data = {};

        this.init = function (alreadyRunning) {

            if (alreadyRunning && graph.svg) {
                graph.chart.remove()
            }

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
            console.log(graphSelector);

            graph.chart = bb.generate({
                data: {
                    columns: graph._data,
                    type: "pie",
                    onclick: function (d, i) { console.log("onclick", d, i); },
                    onover: function (d, i) { console.log("onover", d, i); },
                    onout: function (d, i) { console.log("onout", d, i); }
                },
                legend: {
                    show: false
                },
                pie: {
                    label: {
                        format: function (value, ratio, id) {
                            return value;
                        }
                    }
                },
                bindto: graphSelector
            });

        };

        this.requestData = function (dataUrl, callback) {
            d3.json(dataUrl, function (res) {
                graph._data = res.data;
                if (typeof callback === 'function') {
                    callback();
                }
            });
        };
    };
    return QuantitativePlot;
}(QuantitativePlot || {});

var QuantitativePlot = function (QuantitativePlot) {
    /**
     * Donut chart rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    QuantitativePlot.donutChart = function (dataUrl, graphSelector, refreshInterval) {

        var graph = this;
        this._data = {};

        this.init = function (alreadyRunning) {

            if (alreadyRunning && graph.svg) {
                graph.chart.remove()
            }

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
            console.log(graphSelector);

            graph.chart = bb.generate({
                data: {
                    columns: graph._data,
                    type: "donut",
                    onclick: function (d, i) { console.log("onclick", d, i); },
                    onover: function (d, i) { console.log("onover", d, i); },
                    onout: function (d, i) { console.log("onout", d, i); }
                },
                donut: {
                    title: "",
                    label: {
                        format: function (value, ratio, id) {
                            return value;
                        }
                    }
                },
                legend: {
                    show: false
                },
                bindto: graphSelector
            });

        };

        this.requestData = function (dataUrl, callback) {
            d3.json(dataUrl, function (res) {
                graph._data = res.data;
                if (typeof callback === 'function') {
                    callback();
                }
            });
        };
    };
    return QuantitativePlot;
}(QuantitativePlot || {});
