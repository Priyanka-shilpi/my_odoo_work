odoo.define('your_module.pie_chart_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var Chart = require('Chart'); // ensure Chart.js is loaded

    var PieChartWidget = AbstractField.extend({
        template: 'YourModule.PieChartWidget',

        _render: function () {
            this._super.apply(this, arguments);
            var data = this.value;

            if (!data) return;

            var canvas = document.createElement('canvas');
            this.$el.empty().append(canvas);

            new Chart(canvas.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.values,
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#8BC34A']
                    }]
                }
            });
        }
    });

    fieldRegistry.add('pie_chart_widget', PieChartWidget);
});
