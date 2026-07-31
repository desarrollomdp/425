// Variables globales
let allCourses = [];
let allUsers = [];

// --- FORMATTING UTILS ---
function formatDate(dateString) {
    if (!dateString) return 'Sin fecha';
    const [year, month, day] = dateString.split('-');
    return `${day}/${month}/${year}`;
}

// --- MODAL TODOS LOS USUARIOS ---
window.abrirModalTodosUsuarios = function () {
    $('#modalTodosUsuarios').removeClass('hidden').addClass('flex');
    $('#modalTodosUsuariosBody').html(`
        <div class="flex flex-col items-center justify-center py-12">
            <div class="w-16 h-16 border-4 border-slate-100 border-t-primary rounded-full animate-spin mb-4"></div>
            <h6 class="text-slate-500 font-bold">Cargando lista de usuarios...</h6>
        </div>
    `);

    $.ajax({
        url: '/todos_los_usuarios/',
        method: 'GET',
        success: function (data) {
            allUsers = data;
            renderUsersList(allUsers);
        },
        error: function (err) {
            console.error("Error cargando usuarios", err);
            $('#modalTodosUsuariosBody').html(`
                <div class="bg-red-50 p-6 rounded-2xl text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-3"></i>
                    <p class="text-red-700 font-bold">Error al cargar los usuarios.</p>
                </div>
            `);
        }
    });
};

window.cerrarModalTodosUsuarios = function () {
    $('#modalTodosUsuarios').addClass('hidden').removeClass('flex');
    $('#busqueda-usuarios-modal').val('');
};

function renderUsersList(users) {
    const container = $('#modalTodosUsuariosBody');
    container.empty();

    if (users.length === 0) {
        container.html(`
            <div class="bg-blue-50 p-6 rounded-2xl text-center text-blue-700 font-bold">
                No se encontraron usuarios.
            </div>
        `);
        return;
    }

    let html = `
        <div class="overflow-x-auto">
            <table class="w-full text-left border-separate border-spacing-y-3">
                <thead>
                    <tr class="text-xs font-black uppercase tracking-widest text-slate-400">
                        <th class="px-4 pb-2">Usuario</th>
                        <th class="px-4 pb-2">Email</th>
                        <th class="px-4 pb-2">Rol</th>
                        <th class="px-4 pb-2">DNI</th>
                    </tr>
                </thead>
                <tbody>
    `;

    users.forEach(user => {
        html += `
            <tr class="bg-slate-50 hover:bg-white hover:shadow-lg transition-all duration-300">
                <td class="px-4 py-4 rounded-l-2xl border-y border-l border-slate-100">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                            ${user.first_name ? user.first_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <div class="font-bold text-slate-800 text-sm">${user.first_name} ${user.last_name}</div>
                            <div class="text-[10px] text-slate-400 font-medium">@${user.username}</div>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-4 border-y border-slate-100">
                    <span class="text-slate-600 text-xs font-medium">${user.email}</span>
                </td>
                <td class="px-4 py-4 border-y border-slate-100">
                    <span class="px-3 py-1 bg-slate-200 text-slate-600 text-[10px] font-black uppercase rounded-lg">
                        ${user.rol}
                    </span>
                </td>
                <td class="px-4 py-4 rounded-r-2xl border-y border-r border-slate-100">
                    <span class="text-slate-800 text-xs font-bold font-mono">${user.dni || '---'}</span>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    container.html(html);
}

// --- CURSOS RENDERING ---
function updateProgress(percentage, statusText) {
    const roundedPercentage = Math.round(percentage);
    $('#progress-text').text(roundedPercentage + '%');
    $('#loading-status').text(statusText);
    $('#progress-bar').css('width', roundedPercentage + '%');
}

function updateCounters(courses) {
    $('#counter-cursos').text(courses.length);
    const uniqueStudents = new Set();
    courses.forEach(course => {
        if (course.alumnos_inscriptos) {
            course.alumnos_inscriptos.forEach(studentName => uniqueStudents.add(studentName));
        }
    });
    $('#counter-estudiantes').text(uniqueStudents.size);
}

function renderCourses(courses) {
    const container = $('#dynamic-content');
    container.empty();

    if (courses.length === 0) {
        container.html(`
            <div class="col-span-full bg-blue-50 border-l-4 border-blue-500 p-6 rounded-2xl flex items-center gap-4">
                <i class="fas fa-info-circle text-blue-500 text-xl"></i>
                <p class="text-blue-700 font-bold">No se encontraron cursos con los filtros seleccionados.</p>
            </div>
        `);
        return;
    }

    courses.forEach(course => {
        const card = createCourseCard(course);
        container.append(card);
    });
}

function createCourseCard(course) {
    const estadoBadge = course.cursando
        ? `<span class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-green-100 text-green-600 flex items-center gap-1 w-fit">
                <i class="fas fa-circle text-[8px] animate-pulse"></i> En Curso
           </span>`
        : `<span class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-slate-100 text-slate-500 flex items-center gap-1 w-fit">
                <i class="fas fa-check-circle"></i> Finalizado
           </span>`;

    const diasBadges = course.dias.map(dia =>
        `<span class="px-2 py-1 rounded-lg bg-slate-50 text-slate-500 text-[10px] font-bold border border-slate-100 uppercase">${dia}</span>`
    ).join(' ');

    return `
        <div class="bg-white rounded-[2rem] p-6 shadow-xl shadow-slate-200/40 border border-slate-100 hover:shadow-2xl hover:shadow-primary/5 hover:-translate-y-1 transition-all duration-300 flex flex-col h-full group">
            <div class="flex justify-between items-start mb-4">
                <div class="flex-grow pr-4">
                    <h3 class="text-lg font-black text-slate-800 leading-tight mb-2 group-hover:text-primary transition-colors line-clamp-2">
                        ${course.nombre}
                    </h3>
                    <div class="flex flex-col gap-1.5 mt-3">
                         <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
                            <i class="fas fa-map-marker-alt text-primary/60 w-4"></i>
                            ${course.lugar}
                        </div>
                        <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
                            <i class="fas fa-users text-emerald-500 w-4"></i>
                            ${course.alumnos_inscriptos ? course.alumnos_inscriptos.length : 0} / ${course.max_estudiantes} Estudiantes
                        </div>
                        <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
                            <i class="fas fa-user-circle text-indigo-400 w-4"></i>
                            ${course.instructor.nombre}
                        </div>
                        <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
                            <i class="fas fa-clock text-amber-400 w-4"></i>
                            ${course.horario}
                        </div>
                        <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
                            <i class="fas fa-calendar-alt text-blue-400 w-4"></i>
                            ${formatDate(course.fecha_inicio)} - ${formatDate(course.fecha_fin)}
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-auto pt-4 border-t border-slate-50">
                <div class="flex justify-between items-center mb-4">
                     ${estadoBadge}
                </div>
                
                <p class="text-xs text-slate-400 font-medium line-clamp-2 mb-4 h-8 leading-relaxed">
                    ${course.descripcion || 'Sin descripción disponible para este curso.'}
                </p>

                <div class="flex flex-wrap gap-2 mb-6">
                    ${diasBadges}
                </div>

                <div class="flex items-center justify-between gap-3">
                    <button class="btn-ver-clases w-1/2 py-3 rounded-xl bg-slate-50 text-slate-600 font-bold text-xs hover:bg-slate-100 hover:text-primary transition-all flex items-center justify-center gap-2 group/btn" 
                            data-course-id="${course.id}">
                        <i class="fas fa-list-ul text-slate-400 group-hover/btn:text-primary transition-colors"></i>
                        <span>Ver Clases</span>
                    </button>
                    <button class="btn-ver-alumnos w-1/2 py-3 rounded-xl bg-slate-50 text-slate-600 font-bold text-xs hover:bg-slate-100 hover:text-indigo-600 transition-all flex items-center justify-center gap-2 group/btn" 
                            data-course-id="${course.id}"
                            data-course-name="${course.nombre}">
                        <i class="fas fa-users text-slate-400 group-hover/btn:text-indigo-600 transition-colors"></i>
                        <span>Ver Alumnos</span>
                    </button>
                </div>
                <div class="flex items-center justify-between gap-3 mt-3">
                    <button class="btn-ver-eliminados w-full py-3 rounded-xl bg-orange-50 text-orange-600 font-bold text-xs hover:bg-orange-100 hover:text-orange-700 transition-all flex items-center justify-center gap-2 group/btn" 
                            data-course-id="${course.id}"
                            data-course-name="${course.nombre}">
                        <i class="fas fa-user-times text-orange-400 group-hover/btn:text-orange-700 transition-colors"></i>
                        <span>Estudiantes Eliminados</span>
                    </button>
                </div>
                
                <div id="clases-container-${course.id}" class="hidden mt-4 space-y-3 pt-4 border-t border-slate-100 animate-fade-in">
                    <!-- Clases renderizadas aquí -->
                </div>
            </div>
        </div>
    `;
}

function filterCourses() {
    const nombre = $('#busqueda-nombre').val().toLowerCase();
    const estado = $('#filtro-estado').val();
    const lugar = $('#filtro-lugar').val();
    const anio = $('#filtro-anio').val();

    const filtered = allCourses.filter(course => {
        const matchNombre = course.nombre.toLowerCase().includes(nombre);
        let matchEstado = true;
        if (estado === 'cursando') matchEstado = course.cursando;
        if (estado === 'finalizado') matchEstado = !course.cursando;
        let matchLugar = true;
        if (lugar !== 'todos') matchLugar = course.lugar.toLowerCase() === lugar.toLowerCase();
        let matchAnio = true;
        if (anio !== 'todos') matchAnio = course.fecha_inicio && course.fecha_inicio.startsWith(anio);
        return matchNombre && matchEstado && matchLugar && matchAnio;
    });
    renderCourses(filtered);
}

function renderClassesList(course, container) {
    if (!course.clases || course.clases.length === 0) {
        container.html(`
            <div class="p-3 rounded-xl bg-orange-50 text-orange-600 text-xs font-bold flex items-center gap-2">
                <i class="fas fa-exclamation-triangle"></i> No hay clases registradas.
            </div>
        `);
        return;
    }

    let html = '';
    course.clases.forEach((clase, index) => {
        html += `
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 hover:bg-white hover:border-primary/20 hover:shadow-md transition-all group/clase">
                <div class="flex justify-between items-start gap-3">
                    <div class="flex-grow">
                         <div class="flex items-center gap-2 mb-1">
                            <span class="px-1.5 py-0.5 rounded text-[10px] font-black bg-slate-200 text-slate-600">#${index + 1}</span>
                            <h6 class="text-sm font-bold text-slate-800">${clase.nombre}</h6>
                        </div>
                        <div class="flex items-center gap-3 text-[10px] font-bold text-slate-400">
                            <span class="flex items-center gap-1"><i class="fas fa-calendar-alt"></i> ${clase.fecha}</span>
                        </div>
                    </div>
                    <button class="btn-ver-asistencia p-2 rounded-lg bg-white text-primary border border-slate-200 shadow-sm hover:bg-primary hover:text-white hover:shadow-md transition-all" 
                            data-course-id="${course.id}" data-class-id="${clase.id}" data-class-name="${clase.nombre}" title="Ver Asistencia">
                        <i class="fas fa-users"></i>
                    </button>
                </div>
            </div>
        `;
    });
    container.html(html);
}

function renderStudentsListTable(estudiantes, courseName) {
    if (!estudiantes || estudiantes.length === 0) {
        $('#modalAlumnosBody').html(`
            <div class="bg-indigo-50 p-8 rounded-3xl text-center border border-indigo-100">
                 <div class="w-16 h-16 bg-white rounded-2xl flex items-center justify-center text-indigo-400 text-2xl shadow-sm mx-auto mb-4">
                    <i class="fas fa-users-slash"></i>
                </div>
                <h5 class="text-indigo-900 font-black text-lg mb-1">Sin Inscripciones</h5>
                <p class="text-indigo-600 font-medium text-sm">Este curso aún no tiene alumnos inscritos.</p>
            </div>
        `);
        return;
    }

    let html = `
        <div class="mb-6 flex items-center justify-between"> 
            <div>
                <h6 class="text-sm font-black text-slate-400 uppercase tracking-widest mb-1">Curso</h6>
                <h3 class="text-xl font-black text-slate-800 leading-none">${courseName}</h3>
            </div>
            <div class="bg-indigo-50 text-indigo-600 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wide border border-indigo-100">
                <i class="fas fa-users mr-1"></i> ${estudiantes.length} Alumnos
            </div>
        </div>
        <div class="overflow-hidden rounded-2xl border border-slate-100 shadow-sm">
            <div class="overflow-x-auto">
                <table class="w-full text-left bg-white">
                    <thead class="bg-slate-50 border-b border-slate-100">
                        <tr class="text-[10px] font-black uppercase tracking-widest text-slate-400">
                            <th class="px-6 py-4">Estudiante</th>
                            <th class="px-6 py-4 text-center">Cooperadora</th>
                            <th class="px-6 py-4 text-center">Inscripción Física</th>
                            <th class="px-6 py-4 text-right">Contacto</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-50">
    `;

    estudiantes.forEach(est => {
        const pagoBadge = est.pago_contribucion
            ? `<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-black uppercase border border-emerald-200"><i class="fas fa-check-circle"></i> Pagado</span>`
            : `<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-50 text-rose-500 text-[10px] font-black uppercase border border-rose-100"><i class="fas fa-times-circle"></i> Pendiente</span>`;

        const fisicaBadge = est.inscripcion_fisica
            ? `<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-black uppercase border border-emerald-200"><i class="fas fa-file-contract"></i> Entregado</span>`
            : `<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 text-amber-600 text-[10px] font-black uppercase border border-amber-100"><i class="fas fa-clock"></i> Pendiente</span>`;

        html += `
            <tr class="hover:bg-slate-50/80 transition-colors group">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-sm shadow-sm group-hover:scale-110 transition-transform">${est.nombre.charAt(0).toUpperCase()}</div>
                        <div class="flex flex-col">
                            <span class="font-bold text-slate-700 text-sm group-hover:text-indigo-600 transition-colors">${est.nombre}</span>
                            <span class="text-[10px] font-bold text-slate-400">Ult. acceso: ${est.ultimo_login}</span>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 text-center">${pagoBadge}</td>
                <td class="px-6 py-4 text-center">${fisicaBadge}</td>
                <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                         ${est.telefono && est.telefono !== 'No disponible' ? `
                            <a href="https://wa.me/${est.telefono.replace(/[^0-9]/g, '')}" target="_blank" class="inline-flex w-8 h-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200 hover:bg-emerald-500 hover:text-white hover:border-emerald-500 hover:shadow-md transition-all" title="WhatsApp"><i class="fab fa-whatsapp"></i></a>
                         ` : ''}
                         <a href="/mensajes/chat/${est.id}/" class="inline-flex w-8 h-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-200 hover:bg-indigo-500 hover:text-white hover:border-indigo-500 hover:shadow-md transition-all" title="Enviar Mensaje Interno"><i class="fas fa-comment-dots"></i></a>
                        ${est.inscripcion_id ? `<a href="/cursos/ver_inscripcion_detalle/${est.inscripcion_id}/" target="_blank" class="inline-flex w-8 h-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600 border border-amber-200 hover:bg-amber-500 hover:text-white hover:border-amber-500 hover:shadow-md transition-all" title="Ver Inscripción"><i class="fas fa-file-contract"></i></a>` : ''}
                    </div>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div></div><div class="mt-4 flex justify-end"><button onclick="$('#modalAlumnos').addClass('hidden')" class="px-6 py-2.5 rounded-xl bg-slate-100 text-slate-600 font-bold text-xs hover:bg-slate-200 transition-colors">Cerrar Listado</button></div>`;
    $('#modalAlumnosBody').html(html);
}

function updateModalProgress(percentage, statusText) {
    const roundedPercentage = Math.round(percentage);
    $('#modal-progress-bar').css('width', roundedPercentage + '%');
    $('#modal-loading-status').text(statusText);
}

function renderAttendanceTable(estudiantes, statusMap, className) {
    if (!estudiantes || estudiantes.length === 0) {
        $('#modalAlumnosBody').html(`<div class="bg-blue-50 p-6 rounded-2xl text-center"><i class="fas fa-users-slash text-blue-400 text-4xl mb-3"></i><p class="text-blue-700 font-bold">No hay estudiantes inscritos en este curso.</p></div>`);
        return;
    }

    let html = `<div class="mb-6 flex items-center gap-2"><span class="bg-primary/10 text-primary px-3 py-1 rounded-lg text-sm font-black uppercase tracking-wide">Clase: ${className}</span></div><div class="overflow-x-auto"><table class="w-full text-left border-separate border-spacing-y-3"><thead><tr class="text-xs font-black uppercase tracking-widest text-slate-400"><th class="px-4 pb-2">Estudiante</th><th class="px-4 pb-2">DNI</th><th class="px-4 pb-2 text-center">Estado</th><th class="px-4 pb-2">Asistencia Global</th><th class="px-4 pb-2">Detalle</th></tr></thead><tbody class="space-y-4">`;

    estudiantes.forEach(est => {
        const estado = statusMap[est.nombre] || 'Sin registro';
        let estadoBadge = '';
        switch (estado.toLowerCase()) {
            case 'presente': estadoBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-green-100 text-green-700 text-[10px] font-black uppercase"><i class="fas fa-check"></i> Presente</span>'; break;
            case 'ausente': estadoBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-red-100 text-red-700 text-[10px] font-black uppercase"><i class="fas fa-times"></i> Ausente</span>'; break;
            case 'media_falta': estadoBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-orange-100 text-orange-700 text-[10px] font-black uppercase"><i class="fas fa-minus"></i> Media F.</span>'; break;
            default: estadoBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-500 text-[10px] font-black uppercase"><i class="fas fa-question"></i> Sin Reg.</span>';
        }

        const porcentaje = parseFloat(est.promedio);
        const porcentajeColor = porcentaje < 80 ? 'text-red-500' : 'text-green-500';
        const barColor = porcentaje < 80 ? 'bg-red-500' : 'bg-green-500';

        html += `
            <tr class="bg-slate-50 hover:bg-white hover:shadow-lg hover:scale-[1.01] transition-all duration-300 group">
                <td class="px-4 py-4 rounded-l-2xl border-y border-l border-slate-100 group-hover:border-primary/10">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-slate-700 font-bold shadow-sm">${est.nombre.charAt(0).toUpperCase()}</div>
                        <span class="font-bold text-slate-700 text-sm">${est.nombre}</span>
                    </div>
                </td>
                <td class="px-4 py-4 border-y border-slate-100 group-hover:border-primary/10"><span class="text-slate-500 text-xs font-bold font-mono">${est.dni}</span></td>
                <td class="px-4 py-4 text-center border-y border-slate-100 group-hover:border-primary/10">${estadoBadge}</td>
                <td class="px-4 py-4 border-y border-slate-100 group-hover:border-primary/10">
                    <div class="flex items-center gap-3">
                        <div class="w-24 h-2 bg-slate-200 rounded-full overflow-hidden"><div class="h-full ${barColor}" style="width: ${porcentaje}%"></div></div>
                        <span class="${porcentajeColor} text-xs font-black">${est.promedio}%</span>
                    </div>
                </td>
                <td class="px-4 py-4 rounded-r-2xl border-y border-r border-slate-100 group-hover:border-primary/10"><span class="bg-white px-2 py-1 rounded border border-slate-200 text-[10px] font-mono text-slate-500">${est.detalle || '-'}</span></td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    $('#modalAlumnosBody').html(html);
}

function renderEstudiantesEliminadosListTable(estudiantes, courseName) {
    if (!estudiantes || estudiantes.length === 0) {
        $('#modalAlumnosBody').html(`
            <div class="bg-orange-50 p-8 rounded-3xl text-center border border-orange-100">
                 <div class="w-16 h-16 bg-white rounded-2xl flex items-center justify-center text-orange-400 text-2xl shadow-sm mx-auto mb-4">
                    <i class="fas fa-user-slash"></i>
                </div>
                <h5 class="text-orange-900 font-black text-lg mb-1">Sin Registros</h5>
                <p class="text-orange-600 font-medium text-sm">No hay estudiantes eliminados registrados en este curso.</p>
            </div>
        `);
        return;
    }

    let html = `
        <div class="mb-6 flex items-center justify-between"> 
            <div>
                <h6 class="text-sm font-black text-orange-400 uppercase tracking-widest mb-1">Curso</h6>
                <h3 class="text-xl font-black text-slate-800 leading-none">${courseName}</h3>
            </div>
            <div class="bg-orange-50 text-orange-600 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wide border border-orange-100">
                <i class="fas fa-user-times mr-1"></i> ${estudiantes.length} Eliminados
            </div>
        </div>
        <div class="overflow-hidden rounded-2xl border border-slate-100 shadow-sm">
            <div class="overflow-x-auto">
                <table class="w-full text-left bg-white">
                    <thead class="bg-slate-50 border-b border-slate-100">
                        <tr class="text-[10px] font-black uppercase tracking-widest text-slate-400">
                            <th class="px-6 py-4">Estudiante</th>
                            <th class="px-6 py-4">Instructor Respon.</th>
                            <th class="px-6 py-4">Fecha/Hora</th>
                            <th class="px-6 py-4 w-1/3">Motivo</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-50">
    `;

    estudiantes.forEach(est => {
        html += `
            <tr class="hover:bg-slate-50/80 transition-colors group">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center font-bold text-sm shadow-sm group-hover:scale-110 transition-transform">${est.nombre.charAt(0).toUpperCase()}</div>
                        <div class="flex flex-col">
                            <span class="font-bold text-slate-700 text-sm group-hover:text-orange-600 transition-colors">${est.nombre}</span>
                            <span class="text-[10px] font-bold text-slate-400">${est.email}</span>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="text-slate-600 text-xs font-bold">${est.instructor}</span>
                </td>
                <td class="px-6 py-4">
                    <span class="text-slate-500 text-xs font-bold"><i class="fas fa-calendar-alt mr-1"></i> ${est.fecha}</span>
                </td>
                <td class="px-6 py-4 text-xs text-slate-600 font-medium">
                    ${est.motivo}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div></div><div class="mt-4 flex justify-end"><button onclick="$('#modalAlumnos').addClass('hidden')" class="px-6 py-2.5 rounded-xl bg-slate-100 text-slate-600 font-bold text-xs hover:bg-slate-200 transition-colors">Cerrar Listado</button></div>`;
    $('#modalAlumnosBody').html(html);
}

// --- ASYNC DATA FETCHING ---
function loadCourses() {
    $('#loading-indicator').removeClass('hidden').addClass('flex');
    $('#dynamic-content').addClass('hidden');
    updateProgress(0, 'Iniciando carga...');

    $.ajax({
        url: '/cursos/obtener_cursos_json/',
        method: 'GET',
        xhr: function () {
            const xhr = new window.XMLHttpRequest();
            let progress = 0;
            const progressInterval = setInterval(function () {
                if (progress < 90) {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90;
                    updateProgress(progress, 'Cargando cursos y asistencias...');
                }
            }, 200);
            xhr.addEventListener("loadend", function () { clearInterval(progressInterval); });
            return xhr;
        },
        success: function (data) {
            updateProgress(95, 'Procesando datos...');
            allCourses = data;
            renderCourses(allCourses);
            updateCounters(allCourses);
            updateProgress(100, 'Carga completada');
            setTimeout(function () {
                $('#loading-indicator').removeClass('flex').addClass('hidden');
                $('#dynamic-content').removeClass('hidden');
            }, 500);
        },
        error: function (err) {
            console.error("Error cargando cursos", err);
            updateProgress(0, 'Error en la carga');
            setTimeout(function () {
                $('#loading-indicator').removeClass('flex').addClass('hidden');
                $('#dynamic-content').removeClass('hidden').html(`<div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl w-full col-span-full"><div class="flex"><div class="flex-shrink-0"><i class="fas fa-exclamation-circle text-red-500"></i></div><div class="ml-3"><p class="text-sm text-red-700 font-bold">Error al cargar los cursos. Por favor, recarga la página.</p></div></div></div>`);
            }, 500);
        }
    });
}

function loadSidebarMessages() {
    $.ajax({
        url: '/mensajes/resumen/',
        success: function (response) {
            renderSidebarMessages(response.conversations);
            const totalUnread = response.total_unread;
            const badge = $('#badge-total-mensajes');
            if (totalUnread > 0) {
                badge.text(totalUnread).removeClass('hidden');
                $('#counter-mensajes').text(totalUnread);
            } else {
                badge.addClass('hidden');
                $('#counter-mensajes').text(0);
            }
        }
    });
}

function renderSidebarMessages(conversations) {
    const container = $('#sidebar-messages-list');
    container.empty();
    if (conversations.length === 0) {
        container.html(`<div class="text-center py-4 bg-slate-50 rounded-xl border border-slate-100 border-dashed"><p class="text-[10px] font-bold text-slate-400">No hay mensajes recientes.</p></div>`);
        return;
    }

    conversations.slice(0, 5).forEach(conv => {
        const timeAgo = new Date(conv.ultima_fecha).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
        const badgeUnread = conv.unread_count > 0 ? `<span class="w-2 h-2 bg-red-500 rounded-full border border-white shadow-sm absolute top-0 right-0"></span>` : '';
        const item = `
            <div class="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group relative" onclick="abrirChat(${conv.usuario_id}, '${conv.nombre}', '${conv.avatar || ''}')">
                <div class="relative flex-shrink-0">
                     <div class="w-10 h-10 rounded-full bg-indigo-50 text-indigo-500 flex items-center justify-center font-bold text-sm overflow-hidden border border-slate-100 group-hover:border-indigo-200 transition-colors">${conv.avatar ? `<img src="${conv.avatar}" class="w-full h-full object-cover">` : conv.nombre.charAt(0).toUpperCase()}</div>
                    ${badgeUnread}
                </div>
                <div class="flex-grow min-w-0">
                    <div class="flex justify-between items-baseline mb-0.5">
                        <h6 class="text-xs font-bold text-slate-700 truncate pr-2 group-hover:text-indigo-600 transition-colors">${conv.nombre}</h6>
                        <span class="text-[10px] font-medium text-slate-400 flex-shrink-0">${timeAgo}</span>
                    </div>
                    <p class="text-[10px] text-slate-500 truncate ${conv.unread_count > 0 ? 'font-bold text-slate-800' : ''}">${conv.unread_count > 0 ? `<span class="text-indigo-500 mr-1"><i class="fas fa-circle text-[6px]"></i></span>` : ''} ${conv.ultimo_mensaje}</p>
                </div>
            </div>
        `;
        container.append(item);
    });
}

// --- GLOBAL CHAT FUNCTIONS ---
window.abrirChat = function (userId, userName, userAvatar) {
    $('#chat-header-name').text(userName);
    const avatarHtml = userAvatar && userAvatar !== 'null' && userAvatar !== '' ? `<img src="${userAvatar}" class="w-full h-full object-cover">` : `<span class="text-lg font-bold text-slate-400">${userName.charAt(0).toUpperCase()}</span>`;
    $('#chat-header-avatar').html(avatarHtml);
    $('#modalChat').removeClass('hidden').addClass('flex');
    $('#chat-loader').removeClass('hidden');
    $('#chat-iframe').attr('src', `/mensajes/chat/${userId}/?embed=true`);
};

window.cerrarModalChat = function () {
    $('#modalChat').addClass('hidden').removeClass('flex');
    $('#chat-iframe').attr('src', '');
    loadSidebarMessages();
};

// --- INITIALIZATION ---
$(document).ready(function () {
    loadCourses();
    loadSidebarMessages();
    setInterval(loadSidebarMessages, 30000);

    // Filter Listeners
    $('#busqueda-nombre, #filtro-estado, #filtro-lugar, #filtro-anio').on('input change', function () {
        filterCourses();
    });

    $('#busqueda-usuarios-modal').on('input', function () {
        const query = $(this).val().toLowerCase();
        const filtered = allUsers.filter(user => {
            const fullName = `${user.first_name} ${user.last_name}`.toLowerCase();
            const username = user.username.toLowerCase();
            const dni = (user.dni || '').toString();
            return fullName.includes(query) || username.includes(query) || dni.includes(query);
        });
        renderUsersList(filtered);
    });

    // Event Delegation
    $(document).on('click', '.btn-ver-clases', function () {
        const courseId = $(this).data('course-id');
        const container = $(`#clases-container-${courseId}`);
        const btn = $(this);
        if (!container.hasClass('hidden')) {
            container.slideUp(200, function () { container.addClass('hidden'); });
            btn.removeClass('bg-primary text-white shadow-lg shadow-primary/30').addClass('bg-slate-50 text-slate-600');
            btn.html('<i class="fas fa-list-ul text-slate-400 group-hover/btn:text-primary"></i><span>Ver Clases</span>');
        } else {
            const course = allCourses.find(c => c.id === courseId);
            renderClassesList(course, container);
            container.removeClass('hidden').hide().slideDown(300);
            btn.removeClass('bg-slate-50 text-slate-600').addClass('bg-primary text-white shadow-lg shadow-primary/30');
            btn.html('<i class="fas fa-chevron-up"></i><span>Ocultar Clases</span>');
        }
    });

    $(document).on('click', '.btn-ver-alumnos', function () {
        const courseId = $(this).data('course-id');
        const courseName = $(this).data('course-name');
        $('#modalAlumnos').removeClass('hidden').addClass('flex');
        $('#modalAlumnosBody').html(`<div class="flex flex-col items-center justify-center py-12"><div class="w-16 h-16 border-4 border-slate-100 border-t-indigo-500 rounded-full animate-spin mb-4"></div><h6 class="text-slate-500 font-bold">Cargando lista de alumnos: <span class="text-indigo-500">${courseName}</span>...</h6><div class="w-64 h-2 bg-slate-100 rounded-full mt-4 overflow-hidden"><div id="modal-progress-bar" class="h-full bg-indigo-500 transition-all duration-300" style="width: 0%"></div></div><p class="text-xs text-slate-400 font-bold mt-2">Consultando base de datos...</p></div>`);
        let prog = 0;
        const interval = setInterval(() => { if (prog < 90) { prog += Math.random() * 20; $('#modal-progress-bar').css('width', prog + '%'); } }, 100);
        $.ajax({
            url: `/cursos/curso/${courseId}/estudiantes/json/`,
            success: function (response) { clearInterval(interval); $('#modal-progress-bar').css('width', '100%'); setTimeout(() => { renderStudentsListTable(response.estudiantes, courseName); }, 300); },
            error: function () { clearInterval(interval); $('#modalAlumnosBody').html(`<div class="bg-red-50 p-6 rounded-2xl flex flex-col items-center justify-center text-center gap-3"><i class="fas fa-exclamation-triangle text-red-500 text-3xl"></i><span class="text-red-700 font-bold">Error al obtener la lista de alumnos.</span></div>`); }
        });
    });

    $(document).on('click', '.btn-ver-eliminados', function () {
        const courseId = $(this).data('course-id');
        const courseName = $(this).data('course-name');
        $('#modalAlumnos').removeClass('hidden').addClass('flex');
        $('#modalAlumnosBody').html(`<div class="flex flex-col items-center justify-center py-12"><div class="w-16 h-16 border-4 border-slate-100 border-t-orange-500 rounded-full animate-spin mb-4"></div><h6 class="text-slate-500 font-bold">Cargando lista de eliminados: <span class="text-orange-500">${courseName}</span>...</h6><div class="w-64 h-2 bg-slate-100 rounded-full mt-4 overflow-hidden"><div id="modal-progress-bar" class="h-full bg-orange-500 transition-all duration-300" style="width: 0%"></div></div><p class="text-xs text-slate-400 font-bold mt-2">Consultando base de datos...</p></div>`);
        let prog = 0;
        const interval = setInterval(() => { if (prog < 90) { prog += Math.random() * 20; $('#modal-progress-bar').css('width', prog + '%'); } }, 100);
        $.ajax({
            url: `/cursos/curso/${courseId}/estudiantes_eliminados/json/`,
            success: function (response) { clearInterval(interval); $('#modal-progress-bar').css('width', '100%'); setTimeout(() => { renderEstudiantesEliminadosListTable(response.estudiantes_eliminados, courseName); }, 300); },
            error: function () { clearInterval(interval); $('#modalAlumnosBody').html(`<div class="bg-red-50 p-6 rounded-2xl flex flex-col items-center justify-center text-center gap-3"><i class="fas fa-exclamation-triangle text-red-500 text-3xl"></i><span class="text-red-700 font-bold">Error al obtener la lista de alumnos eliminados.</span></div>`); }
        });
    });

    $(document).on('click', '.btn-ver-asistencia', function () {
        const courseId = $(this).data('course-id');
        const classId = $(this).data('class-id');
        const className = $(this).data('class-name');
        $('#modalAlumnos').removeClass('hidden').addClass('flex');
        $('#modalAlumnosBody').html(`<div class="flex flex-col items-center justify-center py-12"><div class="w-16 h-16 border-4 border-slate-100 border-t-primary rounded-full animate-spin mb-4"></div><h6 class="text-slate-500 font-bold">Cargando asistencias para: <span class="text-primary">${className}</span>...</h6><div class="w-64 h-2 bg-slate-100 rounded-full mt-4 overflow-hidden"><div id="modal-progress-bar" class="h-full bg-primary transition-all duration-300" style="width: 0%"></div></div><p class="text-xs text-slate-400 font-bold mt-2" id="modal-loading-status">Iniciando...</p></div>`);
        let modalProgress = 0;
        const modalProgressInterval = setInterval(function () { if (modalProgress < 90) { modalProgress += Math.random() * 20; if (modalProgress > 90) modalProgress = 90; updateModalProgress(modalProgress, 'Obteniendo datos...'); } }, 150);
        $.ajax({
            url: `/cursos/promedio_asistencias/${courseId}/`,
            success: function (response) {
                clearInterval(modalProgressInterval);
                updateModalProgress(100, 'Datos procesados');
                const promedios = response.promedios;
                const course = allCourses.find(c => c.id === courseId);
                const classAttendances = course.asistencias.filter(a => a.clase_id === classId);
                const statusMap = {};
                classAttendances.forEach(a => { statusMap[a.estudiante] = a.estado; });
                setTimeout(function () { renderAttendanceTable(promedios, statusMap, className); }, 300);
            },
            error: function () { clearInterval(modalProgressInterval); $('#modalAlumnosBody').html(`<div class="bg-red-50 p-4 rounded-2xl flex items-center gap-3"><i class="fas fa-exclamation-triangle text-red-500 text-xl"></i><span class="text-red-700 font-bold">Error al cargar los datos. Intenta nuevamente.</span></div>`); }
        });
    });
});
