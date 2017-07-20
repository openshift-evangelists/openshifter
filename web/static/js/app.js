var processSchemaSection = function (prefix, root, struct) {
    var html = '';
    $.each(root, function (index, field) {
        if(field.type === 'section') {
            struct[field.name] = {};
            html += '<fieldset class="form-group"><legend>' + field.display + '</legend>';
            html += processSchemaSection(prefix + '.' + field.name, field.properties, struct[field.name]);
            html += '</fieldset>';
        } else if (field.type === 'string') {
            if (field.default === undefined) field.default = '';
            html += '<div class="form-group">';
            html += '<label for="' + field.name + '">' + field.display + '</label>';
            html += '<input type="text" class="form-control" id="' + field.name + '" v-model="' + prefix + '.' + field.name + '">';
            html += '</div>';

            struct[field.name] = field.default;
        } else if (field.type === 'integer') {
            if (field.default === undefined) field.default = 0;
            html += '<div class="form-group">';
            html += '<label for="' + field.name + '">' + field.display + '</label>';
            html += '<input type="text" class="form-control" id="' + field.name + '" v-model="' + prefix + '.' + field.name + '">';
            html += '</div>';

            struct[field.name] = field.default;
        } else if (field.type === 'boolean') {
            if (field.default === undefined) field.default = false;
            html += '<div class="form-group">';
            html += '<label for="' + field.name + '">' + field.display + '</label>';
            html += '<input type="text" class="form-control" id="' + field.name + '" v-model="' + prefix + '.' + field.name + '">';
            html += '</div>';

            struct[field.name] = field.default;
        }
    });
    return html;
};

Vue.component('dashboard-view', function (resolve, reject) {
    $.get('/static/views/dashboard.html', function(data){
        resolve({
            template: data,
            data: function() {
                return {
                    message: 'hi'
                }
            }
        });
    });
});

Vue.component('generator-view', function (resolve, reject) {
    $.get('/static/views/generator.html', function(data){
        $.get('/schema.yml', function(schema) {
            schema = jsyaml.load(schema);
            var struct = {};
            var result = processSchemaSection('struct', schema.properties, struct);
            result = data.toString().replace('[[form]]', result);
            resolve({
                template: result,
                data: function() {
                    return {
                        struct: struct
                    }
                },
                computed: {
                    yaml: function () {
                        return window.jsyaml.dump(this.struct);
                    }
                }
            });
        });
    });
});

Vue.component('new-deployment-view', function (resolve, reject) {
    $.get('/static/views/new-deployment.html', function(template){
        $.get('/deployments', function(deployments){
            resolve({
                    template: template,
                    data: function() {
                        return {
                            deployments: deployments
                        }
                    },
                    methods: {
                        new_deployment: function (deployment) {
                            var content = $('#content');
                            content.html('');
                            var pre = $('<pre></pre>');
                            content.append(pre);
                            var ws = new WebSocket("ws://localhost:5000/stream/" + deployment);
                            ws.onmessage = function(event) {
                                var data = JSON.parse(event.data);
                                pre.prepend(data.line);
                            };
                            $.post('/deployments/' + deployment, function(result) {
                            });
                        },
                        destroy_deployment: function (deployment) {
                            var content = $('#content');
                            content.html('');
                            var pre = $('<pre></pre>');
                            content.append(pre);
                            var ws = new WebSocket("ws://localhost:5000/stream/" + deployment);
                            ws.onmessage = function(event) {
                                var data = JSON.parse(event.data);
                                pre.prepend(data.line);
                            };
                            $.ajax({
                                url: '/deployments/' + deployment,
                                type: 'DELETE',
                                success: function(result) {
                                }
                            });
                        }
                    }
            });
        });
    });
});

const Dashboard = {
    template: '<dashboard-view></dashboard-view>'
};

const Generator = {
    template: '<generator-view></generator-view>'
};

const NewDeployment = {
    template: '<new-deployment-view></new-deployment-view>'
};

const routes = [
  { path: '/', component: Dashboard },
  { path: '/generator', component: Generator },
  { path: '/deploy', component: NewDeployment }
];

const router = new VueRouter({
  routes: routes
});

const openshifter = new Vue({
  router: router
}).$mount('#app');