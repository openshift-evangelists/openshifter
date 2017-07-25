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