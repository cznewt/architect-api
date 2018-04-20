
var RelationalPlot = function(RelationalPlot){
    /**
     * Sunburst rendering method
     *
     * Adapted from https://bl.ocks.org/d3noob/d316a488cae262ae24e6ca897b209f9e
     *
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.sunburst = function(dataUrl, graphSelector, refreshInterval){

        var width,
            height,
            maxRadius,
            formatNumber = d3.format(',d'),
            x = d3.scaleLinear().range([0, 2 * Math.PI]).clamp(true),
            y,
            color = d3.scaleOrdinal(d3.schemeCategory20),
            partition = d3.partition(),
            arc,
            graph = this;

        this._data = {};

        this.init = function(alreadyRunning){
            if(alreadyRunning && graph.svg) {
                graph.svg.remove();
            }
            width =  $(graphSelector).innerWidth();
            height = $(graphSelector).innerHeight();
            maxRadius = Math.min(width, height) / 2 - 5;
            y = d3.scaleSqrt().range([maxRadius * .1, maxRadius]);
            arc = d3.arc().startAngle(function (d) {return x(d.x0);})
                .endAngle(function (d) {return x(d.x1);})
                .innerRadius(function (d) {return Math.max(0, y(d.y0));})
                .outerRadius(function (d) {return Math.max(0, y(d.y1));});
            graph.svg = d3.select(graphSelector)
                .append('svg')
                .style('width', width)
                .style('height', height)
                .attr('viewBox', -width / 2 + ' ' + -height / 2 + ' ' + width + ' ' + height)
                .on('click', function () {
                    return graph.focusOn(); // Reset zoom on canvas click
                });

            if(!alreadyRunning){

                graph.requestData(dataUrl, graph.render);
                $(window).on('resize', function(ev){
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

            graph._data.sum(function(d){
                return d.size;
            });

            var slice = graph.svg.selectAll('g.slice')
                .data(partition(graph._data)
                .descendants());

            slice.exit().remove();

            var newSlice = slice.enter()
                .append('g')
                .attr('class', 'slice')
                .on('click', function (d) {
                    d3.event.stopPropagation();
                    graph.focusOn(d);
                });

            newSlice.append('title')
                .text(function (d) {return d.data.name + '\n' + formatNumber(d.value);});

            newSlice.append('path')
                .attr('class', 'main-arc')
                .style('fill', function (d) {
                    //return color((d.children ? d : d.parent).data.name);
                    if(d.data.status == 'active') {
                        return '#77dd77';
                    }
                    if(d.data.status == 'error') {
                        return '#ff6961';
                    }
                    return '#eee';
                }).attr('d', arc);

            newSlice.append('path')
                .attr('class', 'hidden-arc')
                .attr('id', function (_, i) {
                    return 'hiddenArc' + i;
                }).attr('d', graph.middleArcLine);

            var text = newSlice.append('text')
                .attr('display', function (d) {
                    return graph.textFits(d) ? null : 'none';
                });

            // Add white contour
            text.append('textPath')
                .attr('startOffset', '50%')
                .attr('xlink:href', function (_, i) {return '#hiddenArc' + i;})
                .text(function (d) {return d.data.name;})
                .style('fill', 'none').style('stroke', '#fff').style('stroke-width', 5).style('stroke-linejoin', 'round');

            text.append('textPath')
                .attr('startOffset', '50%')
                .attr('xlink:href', function (_, i) {return '#hiddenArc' + i;})
                .text(function (d) {return d.data.name;});

        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                console.log(res);
                if(res){
                    graph._data = d3.hierarchy(res.resources);
                    if(typeof callback === 'function'){
                        callback();
                    }
                }else{
                    console.log("Cannot create topology graph, server returns error: " + res.data);
                }
            });
        };

        this.middleArcLine = function(d) {
            var halfPi = Math.PI / 2;
            var angles = [x(d.x0) - halfPi, x(d.x1) - halfPi];
            var r = Math.max(0, (y(d.y0) + y(d.y1)) / 2);

            var middleAngle = (angles[1] + angles[0]) / 2;
            var invertDirection = middleAngle > 0 && middleAngle < Math.PI; // On lower quadrants write text ccw
            if (invertDirection) {
                angles.reverse();
            }

            var path = d3.path();
            path.arc(0, 0, r, angles[0], angles[1], invertDirection);
            return path.toString();
        };

        this.textFits = function(d) {
            var CHAR_SPACE = 6;

            var deltaAngle = x(d.x1) - x(d.x0);
            var r = Math.max(0, (y(d.y0) + y(d.y1)) / 2);
            var perimeter = r * deltaAngle;

            return d.data.name.length * CHAR_SPACE < perimeter;
        };

        this.focusOn = function() {
            var d = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : { x0: 0, x1: 1, y0: 0, y1: 1 };
            // Reset to top-level if no data point specified
            var transition = graph.svg.transition().duration(750).tween('scale', function () {
                var xd = d3.interpolate(x.domain(), [d.x0, d.x1]),
                    yd = d3.interpolate(y.domain(), [d.y0, 1]);
                return function (t) {
                    x.domain(xd(t));y.domain(yd(t));
                };
            });

            transition.selectAll('path.main-arc').attrTween('d', function (d) {
                return function () {
                    return arc(d);
                };
            });

            transition.selectAll('path.hidden-arc').attrTween('d', function (d) {
                return function () {
                    return graph.middleArcLine(d);
                };
            });

            transition.selectAll('text').attrTween('display', function (d) {
                return function () {
                    return graph.textFits(d) ? null : 'none';
                };
            });

            moveStackToFront(d);

            function moveStackToFront(elD) {
                graph.svg.selectAll('.slice').filter(function (d) {
                    return d === elD;
                }).each(function (d) {
                    this.parentNode.appendChild(this);
                    if (d.parent) {
                        moveStackToFront(d.parent);
                    }
                });
            }
        }
    };
    return RelationalPlot;
}(RelationalPlot || {});
