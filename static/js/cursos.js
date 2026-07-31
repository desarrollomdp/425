// Variables globales para almacenar información del curso y módulo seleccionados
let selectedCourseId = null; // ID del curso seleccionado
let selectedCourseName = ""; // Nombre del curso seleccionado
let selectedModuloName = ""; // Nombre del módulo seleccionado
let selectedModuleId = null; // ID del módulo seleccionado

// Esperamos a que el DOM esté completamente cargado antes de ejecutar el código
document.addEventListener("DOMContentLoaded", function () {

    // Listener global para manejar clics en elementos con la acción "ver-inscripciones"
    document.addEventListener("click", function (e) {
        const target = e.target.closest('[data-action="ver-inscripciones"]');
        if (target && selectedCourseId) {
            // Redirige a la página de inscripciones del curso seleccionado
            window.location.href = `/cursos/inscripciones/?curso=${selectedCourseId}`;
        } else if (target && !selectedCourseId) {
            // Muestra un mensaje si no se ha seleccionado un curso
            mostrarToast("Por favor, seleccioná un curso.", "warning");
        }
    });

    // Cargar la lista de cursos al iniciar la página
    console.log("🏁 DOMContentLoaded: Llamando a fetchCourses()...");
    fetchCourses();
    document.addEventListener('click', function (event) {
        const button = event.target.closest('[data-action="ver-promedios"]');
        if (button) {
            if (!selectedCourseId) {
                return mostrarToast("Selecciona un curso primero", "warning");
            }

            // Asegurar que el modal existe y usar el sistema de Tailwind
            let modal = document.getElementById("modalPromedios");
            if (!modal) {
                const modalHtml = `
                        <div id="modalPromedios" class="fixed inset-0 z-[100] hidden overflow-y-auto">
                            <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onclick="this.parentElement.classList.add('hidden')"></div>
                            <div class="flex min-h-full items-center justify-center p-4">
                                <div class="relative w-full max-w-4xl bg-white rounded-[3rem] shadow-2xl overflow-hidden p-8 lg:p-12 animate-zoom-in">
                                    <h3 class="text-3xl font-black text-slate-800 mb-8 flex items-center gap-4">
                                        <span class="w-12 h-12 bg-green-50 rounded-2xl flex items-center justify-center text-green-600">
                                            <i class="fas fa-percentage"></i>
                                        </span>
                                        Promedios de Asistencia
                                    </h3>
                                    <div id="contenedor-promedios" class="min-h-[300px]">
                                        <div class="flex items-center justify-center p-12">
                                            <i class="fas fa-circle-notch fa-spin text-4xl text-primary"></i>
                                        </div>
                                    </div>
                                    <button type="button" class="absolute top-8 right-8 text-slate-400 hover:text-slate-600"
                                        onclick="document.getElementById('modalPromedios').classList.add('hidden')">
                                        <i class="fas fa-times text-2xl"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                modal = document.getElementById("modalPromedios");
            }

            modal.classList.remove("hidden");
            const contenedor = document.getElementById("contenedor-promedios");
            contenedor.innerHTML = `
                    <div class="flex items-center justify-center p-12">
                        <i class="fas fa-circle-notch fa-spin text-4xl text-primary"></i>
                    </div>
                `;

            fetch(`/reportes/asistencia-curso/${selectedCourseId}/`)
                .then(response => {
                    if (!response.ok) throw new Error("Error en la respuesta del servidor");
                    return response.json();
                })
                .then(data => {
                    if (!data.estudiantes || data.estudiantes.length === 0) {
                        contenedor.innerHTML = `<div class="p-12 text-center text-slate-400 font-bold italic">No hay estudiantes registrados.</div>`;
                        return;
                    }
                    data.estudiantes.sort((a, b) => a.nombre_completo.localeCompare(b.nombre_completo));

                    const tabla = `
                            <div class="overflow-x-auto rounded-3xl border border-slate-100">
                                <table class="w-full text-left border-collapse">
                                    <thead>
                                        <tr class="bg-slate-50">
                                            <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Estudiante</th>
                                            <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">DNI</th>
                                            <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Detalles</th>
                                            <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Asistencia</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-slate-100">
                                        ${data.estudiantes.map(est => `
                                            <tr class="hover:bg-slate-50/50 transition-colors">
                                                <td class="p-6">
                                                    <p class="font-black text-slate-800">${est.nombre_completo}</p>
                                                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">${est.es_pen ? 'Pensión' : 'Regular'}</p>
                                                </td>
                                                <td class="p-6 text-slate-500 font-bold font-mono text-sm">${est.dni}</td>
                                                <td class="p-6">
                                                    <div class="flex gap-2">
                                                        <span class="px-2 py-1 bg-green-50 text-green-600 text-[9px] font-black rounded-md">P: ${est.resumen.clases_presentes}</span>
                                                        <span class="px-2 py-1 bg-rose-50 text-rose-600 text-[9px] font-black rounded-md">A: ${est.resumen.clases_ausentes}</span>
                                                    </div>
                                                </td>
                                                <td class="p-6 text-right">
                                                    <span class="px-4 py-2 ${est.resumen.porcentaje_asistencia >= 75 ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'} rounded-xl font-black text-sm">
                                                        ${est.resumen.porcentaje_asistencia}%
                                                    </span>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        `;
                    contenedor.innerHTML = tabla;
                })
                .catch(error => {
                    contenedor.innerHTML = `<div class="p-8 bg-rose-50 text-rose-500 rounded-2xl font-bold text-center">Error: ${error.message}</div>`;
                });
        }
    });
    const opcionesModulo = document.getElementById("opciones-modulo");
    if (opcionesModulo) {
        document.getElementById("opciones-modulo").addEventListener("click", function (e) {
            const target = e.target.closest("[data-action]");
            if (!target) return;

            const action = target.dataset.action;
            console.log("👉 Acción desde opciones-modulo:", action);

            if (action === "editar-modulo" && selectedModuleId) {
                handleEditModule();
            } else if (action === "eliminar-modulo" && selectedModuleId) {
                handleDeleteModule();
            } else if (action === "ver-notas") {
                if (!selectedModuleId) {
                    mostrarToast("Selecciona un módulo primero", "warning");
                    return;
                }
                handleVerNotas();
            } else if (action === "gestionar-notas") {
                // redirects handled elsewhere
                return;
            } else {
                mostrarToast("Selecciona un módulo primero", "warning");
                console.log("El modulo seleccionado es: ", selectedModuleId)
            }
        });
    }
});

// Listener GLOBAL para formularios dinámicos (Delegación de eventos to the rescue!)
document.addEventListener('submit', function (e) {
    if (e.target && e.target.id === 'editarModuloForm') {
        e.preventDefault();
        console.log("🚀 Interceptado submit de editarModuloForm");
        submitModuleForm(e.target, "editar");
    }
});


// Listener para manejar acciones en los módulos


// Obtener el botón
const crearClaseBtn = document.getElementById("btn-crear-clase");

// Cuando se seleccione un curso, opcionalmente puedes cambiarle el tooltip o habilitarlo
document.addEventListener("cursoSeleccionado", () => {
    console.log("Curso seleccionado:", selectedCourseId, selectedCourseName);
    crearClaseBtn.disabled = false; // si lo tenías deshabilitado
    crearClaseBtn.title = `Crear clase en el curso ${selectedCourseName}`;
});

// Al hacer click en “Crear Clase”
crearClaseBtn.addEventListener("click", function (e) {
    e.preventDefault();       // por si fuera inside form
    if (!selectedCourseId) {
        return mostrarToast("Selecciona un curso primero", "warning");
    }
    // Redirige al endpoint de creación de clase
    window.location.href = `/cursos/crear_clase/${selectedCourseId}/`;
});

// Listener para el botón "Ver Clases"
document.querySelector('[data-action="ver-clases"]').addEventListener("click", function () {
    if (!selectedCourseId) {
        mostrarToast("Selecciona un curso primero", "warning");
        return;
    }

    // Realiza una solicitud para obtener las clases del curso seleccionado
    fetch(`/cursos/ver_clases/${selectedCourseId}/`)
        .then(response => response.text())
        .then(html => {
            const modal = document.getElementById("verClasesModal");
            const modalContent = document.getElementById("verClasesModalContent");
            modalContent.innerHTML = html; // Inserta el contenido en el modal
            modal.classList.remove("hidden"); // Muestra el modal
        })
        .catch(handleError); // Maneja errores
});

// Función para manejar la edición de un módulo
function handleEditModule() {
    fetch(`/cursos/modulo/${selectedModuleId}/editar/`)
        .then(response => response.text())
        .then(html => {
            const modal = document.getElementById("editarModuloModal");
            const modalContent = document.getElementById("editarModuloContent");
            modalContent.innerHTML = html; // Inserta el contenido en el modal
            modal.classList.remove("hidden"); // Muestra el modal

            // Maneja el envío del formulario de edición -> MOVIDO A LISTENER GLOBAL
            // document.getElementById("editarModuloForm").addEventListener("submit", (e) => {
            //    e.preventDefault(); 
            //    submitModuleForm(e.target, "editar"); 
            // });
        })
        .catch(handleError); // Maneja errores
}

// Función para manejar la eliminación de un módulo
function handleDeleteModule() {
    fetch(`/cursos/modulos/eliminar/${selectedModuleId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"), // Token CSRF para seguridad
            "Accept": "application/json", // Especifica que se espera JSON
            "Content-Type": "application/json"
        },
    })
        .then(response => {
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                throw new TypeError("La respuesta no es JSON");
            }
            return response.json(); // Convierte la respuesta a JSON
        })
        .then(data => {
            if (data.success) {
                mostrarToast(data.message, "success"); // Muestra un mensaje de éxito
                fetchModules(selectedCourseId); // Actualiza la lista de módulos
            } else {
                mostrarToast(data.error || "Error desconocido", "danger"); // Muestra un mensaje de error
            }
        })
        .catch(error => {
            console.error("Error:", error);
            mostrarToast(`Error de conexión: ${error.message}`, "danger"); // Muestra un mensaje de error
        });
}

// Función para enviar un formulario de módulo
function submitModuleForm(form, actionType) {
    const formData = new FormData(form); // Crea un objeto FormData con los datos del formulario

    // Mostrar indicador de carga en el botón
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Guardando...';

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value, // Token CSRF
            'Accept': 'application/json', // Especifica que se espera JSON
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json(); // Convierte la respuesta a JSON
            } else {
                throw new Error("La respuesta no es JSON");
            }
        })
        .then(data => {
            if (data.success) {
                mostrarToast(data.message, "success");

                // Cerrar el modal
                const modal = document.getElementById("editarModuloModal");
                if (modal) modal.classList.add("hidden");

                // Actualizar la interfaz
                if (selectedCourseId) {
                    fetchModules(selectedCourseId); // Actualiza sidebar
                    renderCursoDashboard(selectedCourseId); // Actualiza dashboard principal
                }
            } else {
                // Manejo básico de errores de validación
                let errorMessage = "Error al guardar el módulo.";
                if (data.errors) {
                    try {
                        // Intenta parsear si viene como string JSON
                        const errorsObj = typeof data.errors === 'string' ? JSON.parse(data.errors) : data.errors;
                        // Toma el primer error que encuentre
                        const firstField = Object.keys(errorsObj)[0];
                        if (firstField) {
                            const msgs = errorsObj[firstField];
                            errorMessage = `${firstField}: ${msgs[0]?.message || msgs[0]}`;
                        }
                    } catch (e) {
                        console.error("Error al parsear errores", e);
                    }
                }
                mostrarToast(errorMessage, "danger");
            }
        })
        .catch(handleError)
        .finally(() => {
            // Restaurar botón
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
}

// Función para manejar el modal "Ver Notas"
function handleVerNotas() {
    const modal = document.getElementById("verNotasModal");
    const modalContent = document.getElementById("verNotasModalContent");

    // Mostrar modal con loading
    modal.classList.remove("hidden");
    modalContent.innerHTML = `
            <div class="flex items-center justify-center p-12">
                <i class="fas fa-circle-notch fa-spin text-4xl text-primary"></i>
            </div>
        `;

    // Usar el endpoint existente de notas por curso y filtrar por módulo
    fetch(`/cursos/${selectedCourseId}/notas/`)
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener las notas");
            return response.json();
        })
        .then(data => {
            // Filtrar las notas solo del módulo seleccionado
            const notasModulo = data.notas.filter(nota => nota.modulo === selectedModuleName);

            if (!notasModulo || notasModulo.length === 0) {
                modalContent.innerHTML = `
                        <div class="p-12 text-center text-slate-400 font-bold italic">
                            No hay estudiantes con notas en este módulo.
                        </div>
                    `;
                return;
            }

            // Ordenar estudiantes alfabéticamente
            notasModulo.sort((a, b) => a.estudiante.localeCompare(b.estudiante));

            // Crear tabla con las notas
            const tabla = `
                    <div class="overflow-x-auto rounded-3xl border border-slate-100">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="bg-slate-50">
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Estudiante</th>
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Módulo</th>
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Nota</th>
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Estado</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                ${notasModulo.map(nota => {
                const notaValor = parseFloat(nota.nota);
                const aprobado = notaValor >= 70;
                return `
                                        <tr class="hover:bg-slate-50/50 transition-colors">
                                            <td class="p-6">
                                                <p class="font-black text-slate-800">${nota.estudiante}</p>
                                            </td>
                                            <td class="p-6 text-slate-500 font-bold font-mono text-sm">${nota.modulo}</td>
                                            <td class="p-6 text-right">
                                                <span class="px-4 py-2 ${aprobado ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'} rounded-xl font-black text-lg">
                                                    ${notaValor.toFixed(2)}
                                                </span>
                                            </td>
                                            <td class="p-6 text-right">
                                                <span class="px-3 py-1.5 ${aprobado ? 'bg-green-50 text-green-600' : 'bg-rose-50 text-rose-600'} text-[10px] font-black uppercase tracking-widest rounded-full">
                                                    ${aprobado ? 'Aprobado' : 'Desaprobado'}
                                                </span>
                                            </td>
                                        </tr>
                                    `;
            }).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            modalContent.innerHTML = tabla;
        })
        .catch(error => {
            console.error("Error:", error);
            modalContent.innerHTML = `
                    <div class="p-8 bg-rose-50 text-rose-500 rounded-2xl font-bold text-center">
                        Error: ${error.message}
                    </div>
                `;
        });
}

// Exponer la función al scope global para que onclick pueda accederla
window.handleVerNotas = handleVerNotas;

// Listener para el botón "Ver Estudiantes"
document.querySelector('[data-action="ver-estudiantes"]').addEventListener("click", function () {
    if (selectedCourseId) {
        fetchStudents(selectedCourseId);

    } else {
        mostrarToast("Selecciona un curso primero", "warning");
    }
});

// Listener para el botón "Gestionar Notas"
const btnGestionarNotas = document.querySelector('[data-action="gestionar-notas"]');
if (btnGestionarNotas) {
    btnGestionarNotas.addEventListener('click', function (e) {
        e.preventDefault();
        if (selectedModuleId) {
            window.location.href = `/cursos/gestionar_notas/${selectedModuleId}/`;
        } else {
            mostrarToast('Por favor, selecciona un módulo primero.', 'warning');
        }
    });
}



// Listener para el botón "Editar Curso"
document.querySelector('[data-action="editar-curso"]').addEventListener("click", function () {
    if (!selectedCourseId) {
        mostrarToast("Selecciona un curso primero", "warning");
        return;
    }

    fetch(`/cursos/curso/${selectedCourseId}/editar/`)
        .then(response => response.text())
        .then(html => {
            const modal = document.getElementById("editarCursoModal");
            const modalContent = document.getElementById("editarCursoModalContent");
            modalContent.innerHTML = html;
            modal.classList.remove("hidden");
        })
        .catch(error => console.error("Error:", error));
});

const eliminarButtons = document.querySelectorAll(".eliminar-curso");
const eliminarForm = document.getElementById("eliminarCursoForm");
const cursoNombre = document.getElementById("cursoNombre");

eliminarButtons.forEach(button => {
    button.addEventListener("click", function () {
        const cursoId = selectedCourseId;
        const nombre = this.getAttribute("data-nombre");

        // Actualiza el texto en el modal
        cursoNombre.textContent = nombre;

        // Actualiza la acción del formulario con la URL correcta
        eliminarForm.setAttribute("action", `/cursos/curso/${cursoId}/eliminar/`);
    });
});

// Listener para el botón "Guardar Cambios"
// Listener para el botón "Guardar Cambios" (CORREGIDO)
document.getElementById("editarCursoModal").addEventListener("click", function (e) {
    if (e.target.closest('#guardarCambiosCurso')) {
        const form = document.getElementById("editarCursoForm");
        const formData = new FormData(form);

        fetch(`/cursos/curso/${selectedCourseId}/editar/`, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            },
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarToast(data.message, "success");
                    location.reload();
                } else {
                    mostrarToast("Error al actualizar", "danger");
                }
            })
            .catch(error => console.error("Error:", error));

    }
});


// --------------------------------------------------------------------
// Funciones principales
// --------------------------------------------------------------------
// Función para obtener la lista de cursos
function fetchCourses() {
    console.log("🚀 fetchCourses: Iniciando petición...");
    fetch("/cursos/obtener_cursos_json/")
        .then(response => {
            console.log("📡 fetchCourses: Respuesta recibida", response.status);
            return handleResponse(response);
        })
        .then(data => {
            console.log("📦 fetchCourses: Datos recibidos", data);
            displayCourses(data);
        })
        .catch(error => {
            console.error("❌ fetchCourses: Error", error);
            handleError(error);
        });
}
window.fetchCourses = fetchCourses;
window.displayCourses = displayCourses;

// Función para obtener la lista de módulos de un curso
function fetchModules(cursoId) {
    console.log("🚀 fetchModules: Iniciando petición para curso", cursoId);
    fetch(`/cursos/obtener_modulos_por_curso/${cursoId}/`)
        .then(response => {
            console.log("📡 fetchModules: Respuesta recibida", response.status);
            return handleResponse(response);
        })
        .then(data => {
            console.log("📦 fetchModules: Datos recibidos", data);
            displayModules(data);
        })
        .catch(error => {
            console.error("❌ fetchModules: Error", error);
            handleError(error);
        });
}
window.fetchModules = fetchModules;

// Función para mostrar la lista de cursos en la interfaz
function displayCourses(courses) {
    const listaCursos = document.getElementById("lista-cursos");
    listaCursos.innerHTML = "";

    if (courses.length === 0) {
        listaCursos.innerHTML = '<div class="text-xs font-bold text-slate-400 p-4 bg-slate-50 rounded-xl">No tienes cursos asignados.</div>';
        return;
    }

    // Ordenar cursos por fecha de inicio (descendente: más recientes primero)
    courses.sort((a, b) => new Date(b.fecha_inicio) - new Date(a.fecha_inicio));

    let currentYear = null;

    courses.forEach(curso => {
        // Obtener el año de inicio
        const courseYear = new Date(curso.fecha_inicio).getFullYear();

        // Insertar encabezado de año si cambia
        if (courseYear !== currentYear) {
            currentYear = courseYear;
            const yearHeader = document.createElement("li");
            yearHeader.className = "pt-4 pb-2 text-xs font-black uppercase tracking-widest text-slate-400 border-b border-slate-100 mb-2";
            yearHeader.innerText = `Ciclo Lectivo ${currentYear}`;
            listaCursos.appendChild(yearHeader);
        }

        const li = document.createElement("li");
        li.className = "course-item flex items-center justify-between p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all cursor-pointer group border-2 border-transparent";
        li.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-primary/5 group-hover:bg-primary/20 rounded-lg flex items-center justify-center text-primary transition-colors text-xs">
                    <i class="fas fa-bookmark"></i>
                </div>
                <span class="text-sm truncate max-w-[160px]">${curso.nombre}</span>
            </div>
            <i class="fas fa-chevron-right text-[10px] text-slate-300 group-hover:text-primary group-hover:translate-x-1 transition-all"></i>
        `;
        li.dataset.cursoId = curso.id;

        li.addEventListener("click", (e) => {
            selectCourse(curso.id, curso.nombre, e.currentTarget);
        });

        listaCursos.appendChild(li);
    });
}
// Función para seleccionar un curso
window.selectCourse = function (cursoId, cursoNombre, selectedElement) {
    console.log("Seleccionando curso:", cursoId, cursoNombre);
    selectedCourseId = cursoId;
    selectedCourseName = cursoNombre;

    // Resetear selección en el menú
    document.querySelectorAll(".course-item").forEach(item => {
        item.classList.remove("active", "bg-blue-600", "text-white", "border-yellow-400");
        item.classList.add("text-slate-600", "hover:bg-slate-50", "border-transparent");

        // Restaurar iconos y textos internos si es necesario
        const iconContainer = item.querySelector('.w-8');
        if (iconContainer) {
            iconContainer.classList.remove("bg-white/20", "text-white");
            iconContainer.classList.add("bg-primary/5", "text-primary");
        }
    });

    // Resaltar elemento seleccionado
    selectedElement.classList.add("active", "bg-blue-600", "text-white", "border-yellow-400");
    selectedElement.classList.remove("text-slate-600", "hover:bg-slate-50", "border-transparent");

    // Ajustar estilos internos para contraste
    const iconContainer = selectedElement.querySelector('.w-8');
    if (iconContainer) {
        iconContainer.classList.remove("bg-primary/5", "text-primary");
        iconContainer.classList.add("bg-white/20", "text-white");
    }

    // Limpiar estados previos
    selectedModuleId = null;
    document.getElementById("opciones-modulo")?.classList.add("hidden");
    document.getElementById("seccion-modulos")?.classList.add("hidden");

    // Mostrar opciones del curso en el sidebar
    document.getElementById("opciones-curso").classList.remove("hidden");

    // Cargar el Dashboard central del curso
    renderCursoDashboard(cursoId);

    // Actualizar módulos en sidebar (opcional, pero lo mantenemos por consistencia)
    fetchModules(cursoId);

    // 🔥 DISPARAR EL EVENTO "cursoSeleccionado"
    document.dispatchEvent(new Event("cursoSeleccionado"));
}

// Nueva función para renderizar el dashboard central
window.renderCursoDashboard = function (cursoId) {
    const container = document.getElementById('datos-curso');

    // Estado de carga
    container.innerHTML = `
        <div class="bg-white rounded-[2.5rem] p-12 text-center border border-slate-100 shadow-sm animate-pulse">
            <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 text-primary">
                <i class="fas fa-circle-notch fa-spin text-4xl"></i>
            </div>
            <h2 class="text-2xl font-black text-slate-800 mb-2">Cargando Dashboard...</h2>
            <p class="text-slate-400 font-medium">Obteniendo información del curso y módulos.</p>
        </div>
    `;

    fetch(`/cursos/obtener-datos-curso/${cursoId}/`)
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener datos");
            return response.json();
        })
        .then(data => {
            container.innerHTML = `
                <div class="space-y-8 animate-fade-in">
                    <!-- Header del Curso -->
                    <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl shadow-slate-200/40 relative overflow-hidden">
                        <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[5rem] -mr-8 -mt-8"></div>
                        <div class="relative z-10">
                            
                            <h1 class="text-4xl font-black text-slate-800 leading-tight mb-4">${data.nombre}</h1>
                            <p class="text-slate-500 font-medium max-w-2xl mb-8">${data.descripcion || 'Sin descripción disponible.'}</p>
                            
                            <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
                                <div class="p-4 bg-slate-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Inscritos</p>
                                    <p class="text-xl font-black text-slate-800">${data.max_estudiantes - data.vacantes_disponibles}/${data.max_estudiantes}</p>
                                </div>
                                <div class="p-4 bg-emerald-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-1">Grupo de familia</p>
                                    <p class="text-xl font-black text-emerald-600">${data.grupo_familia}</p>
                                </div>
                                <div class="p-4 bg-blue-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-blue-400 mb-1">Inicio</p>
                                    <p class="text-xl font-black text-blue-600">${data.fecha_inicio}</p>
                                </div>
                                <div class="p-4 bg-rose-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-rose-400 mb-1">Fin</p>
                                    <p class="text-xl font-black text-rose-600">${data.fecha_fin}</p>
                                </div>
                                <div class="p-4 bg-purple-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-purple-400 mb-1">Horarios y Creación</p>
                                    <p class="text-sm font-black text-purple-600">${data.dias.join(', ')}</p>
                                    <p class="text-xs font-bold text-slate-500">${data.horario}</p>
                                    <p class="text-[9px] text-slate-400 mt-1 uppercase font-bold tracking-wider">Creado: ${data.fecha_creacion}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Módulos y Acciones -->
                    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                        <!-- Columna Módulos -->
                        <div class="xl:col-span-2 space-y-6">
                            <h5 class="text-xl font-black text-slate-800 flex items-center gap-3">
                                <span class="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center text-green-600 text-sm">
                                    <i class="fas fa-layer-group"></i>
                                </span>
                                Módulos del Curso
                            </h5>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                ${data.modulos.length > 0 ? data.modulos.map(mod => `
                                    <div class="module-card group bg-white p-6 rounded-3xl border border-slate-100 hover:border-primary/30 transition-all hover:shadow-lg hover:shadow-primary/5 cursor-pointer"
                                         onclick="selectModule(${mod.id}, '${mod.nombre}', this)">
                                        <div class="flex justify-between items-start mb-4">
                                            <div class="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400 group-hover:bg-primary/10 group-hover:text-primary transition-all">
                                                <i class="fas fa-folder text-xl"></i>
                                            </div>
                                            <span class="px-3 py-1 bg-slate-100 text-slate-500 text-[9px] font-black uppercase tracking-widest rounded-full">
                                                ID: ${mod.id}
                                            </span>
                                        </div>
                                        <h6 class="text-lg font-black text-slate-800 group-hover:text-primary transition-colors mb-2">${mod.nombre}</h6>
                                        <div class="flex items-center gap-2 mt-4 text-[10px] font-black uppercase tracking-widest">
                                            ${(() => {
                    const total = mod.total_estudiantes || 0;
                    const calificados = mod.estudiantes_con_nota || 0;
                    const faltantes = total - calificados;

                    if (total === 0) {
                        return `<span class="text-slate-400"><i class="fas fa-users-slash mr-1"></i> Sin estudiantes</span>`;
                    }

                    if (faltantes === 0) {
                        return `<span class="text-emerald-500"><i class="fas fa-check-circle mr-1"></i> Completado</span>`;
                    } else {
                        return `<span class="text-rose-500"><i class="fas fa-exclamation-circle mr-1"></i> Falta ${faltantes} de ${total}</span>`;
                    }
                })()}
                                        </div>
                                    </div>
                                `).join('') : `
                                    <div class="col-span-2 p-12 text-center bg-slate-50 rounded-[2rem] border border-dashed border-slate-200">
                                        <p class="font-bold text-slate-400 italic">No hay módulos asignados a este curso.</p>
                                    </div>
                                `}
                            </div>
                        </div>

                        <!-- Columna Acciones Rápidas del Curso -->
                        <div class="space-y-6">
                            <h5 class="text-xl font-black text-slate-800 flex items-center gap-3">
                                <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary text-sm">
                                    <i class="fas fa-bolt"></i>
                                </span>
                                Gestión Rápida
                            </h5>
                            <div class="bg-white rounded-[2rem] border border-slate-100 p-4 space-y-2">
                                <button onclick="fetchStudents(${cursoId})" 
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-users text-primary group-hover:scale-110 transition-transform"></i>
                                    Lista de Estudiantes
                                </button>
                                <button onclick="abrirModalClases(${cursoId})"
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-calendar-check text-cyan-500 group-hover:scale-110 transition-transform"></i>
                                    Calendario de Clases
                                </button>
                                <button onclick="window.location.href='/cursos/inscripciones/?curso=${cursoId}'"
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-clipboard-list text-emerald-600 group-hover:scale-110 transition-transform"></i>
                                    Inscripciones
                                </button>
                                <button onclick="abrirModalEditarCurso(${cursoId})"
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-edit text-yellow-500 group-hover:scale-110 transition-transform"></i>
                                    Editar Curso
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error("Error:", error);
            container.innerHTML = `<div class="p-8 bg-rose-50 text-rose-500 rounded-[2.5rem] font-bold text-center">Error al cargar el dashboard: ${error.message}</div>`;
        });
}

// --------------------------------------------------------------------
// Global Helper Functions (Exposed for onclick events)
// --------------------------------------------------------------------

// Helpers para invocar modales desde el dashboard
window.abrirModalClases = function (id) {
    const modal = document.getElementById("verClasesModal");
    const content = document.getElementById("verClasesModalContent");

    content.innerHTML = `
        <div class="flex items-center justify-center p-12">
            <i class="fas fa-circle-notch fa-spin text-4xl text-primary"></i>
        </div>
    `;
    modal.classList.remove("hidden");

    fetch(`/cursos/ver_clases/${id}/`)
        .then(response => response.text())
        .then(html => {
            content.innerHTML = html;
        });
}

window.abrirModalEditarCurso = function (id) {
    const modal = document.getElementById("editarCursoModal");
    const content = document.getElementById("editarCursoModalContent");

    content.innerHTML = `
        <div class="flex items-center justify-center p-12">
            <i class="fas fa-circle-notch fa-spin text-4xl text-primary"></i>
        </div>
    `;
    modal.classList.remove("hidden");

    fetch(`/cursos/curso/${id}/editar/`)
        .then(response => response.text())
        .then(html => {
            content.innerHTML = html;
        });
}

window.abrirModalEditarModulo = function (id) {
    const modal = document.getElementById("editarModuloModal");
    const content = document.getElementById("editarModuloContent");

    content.innerHTML = `
        <div class="flex items-center justify-center p-12">
            <i class="fas fa-circle-notch fa-spin text-4xl text-amber-500"></i>
        </div>
    `;
    modal.classList.remove("hidden");

    fetch(`/cursos/modulo/${id}/editar/`)
        .then(response => response.text())
        .then(html => {
            content.innerHTML = html;
        });
}

window.eliminarModulo = function (id, nombre) {
    if (!confirm(`¿Estás seguro de que deseas eliminar el módulo "${nombre}"?`)) return;

    fetch(`/cursos/modulos/eliminar/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarToast(data.message, "success");
                // Recargar sidebar y dashboard
                if (selectedCourseId) {
                    fetchModules(selectedCourseId);
                    renderCursoDashboard(selectedCourseId);
                }
            } else {
                mostrarToast(data.error || "Error al eliminar", "danger");
            }
        })
        .catch(handleError);
}

window.handleVerNotas = function () {
    const modal = document.getElementById("verNotasModal");
    const modalContent = document.getElementById("verNotasModalContent");

    // Mostrar modal con loading
    modal.classList.remove("hidden");
    modalContent.innerHTML = `
            <div class="flex items-center justify-center p-12">
                <i class="fas fa-circle-notch fa-spin text-4xl text-primary"></i>
            </div>
        `;

    // Usar el endpoint existente de notas por curso y filtrar por módulo
    fetch(`/cursos/${selectedCourseId}/notas/`)
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener las notas");
            return response.json();
        })
        .then(data => {
            // Filtrar las notas solo del módulo seleccionado
            const notasModulo = data.notas.filter(nota => nota.modulo === selectedModuleName);

            if (!notasModulo || notasModulo.length === 0) {
                modalContent.innerHTML = `
                        <div class="p-12 text-center text-slate-400 font-bold italic">
                            No hay estudiantes con notas en este módulo.
                        </div>
                    `;
                return;
            }

            // Ordenar estudiantes alfabéticamente
            notasModulo.sort((a, b) => a.estudiante.localeCompare(b.estudiante));

            // Crear tabla con las notas
            const tabla = `
                    <div class="overflow-x-auto rounded-3xl border border-slate-100">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="bg-slate-50">
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Estudiante</th>
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Módulo</th>
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Nota</th>
                                    <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Estado</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                ${notasModulo.map(nota => {
                const notaValor = parseFloat(nota.nota);
                const aprobado = notaValor >= 70;
                return `
                                        <tr class="hover:bg-slate-50/50 transition-colors">
                                            <td class="p-6">
                                                <p class="font-black text-slate-800">${nota.estudiante}</p>
                                            </td>
                                            <td class="p-6 text-slate-500 font-bold font-mono text-sm">${nota.modulo}</td>
                                            <td class="p-6 text-right">
                                                <span class="px-4 py-2 ${aprobado ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'} rounded-xl font-black text-lg">
                                                    ${notaValor.toFixed(2)}
                                                </span>
                                            </td>
                                            <td class="p-6 text-right">
                                                <span class="px-3 py-1.5 ${aprobado ? 'bg-green-50 text-green-600' : 'bg-rose-50 text-rose-600'} text-[10px] font-black uppercase tracking-widest rounded-full">
                                                    ${aprobado ? 'Aprobado' : 'Desaprobado'}
                                                </span>
                                            </td>
                                        </tr>
                                    `;
            }).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            modalContent.innerHTML = tabla;
        })
        .catch(error => {
            console.error("Error:", error);
            modalContent.innerHTML = `
                    <div class="p-8 bg-rose-50 text-rose-500 rounded-2xl font-bold text-center">
                        Error: ${error.message}
                    </div>
                `;
        });
}

// --------------------------------------------------------------------
// Funciones principales
// --------------------------------------------------------------------
// Función para obtener la lista de cursos
function fetchCourses() {
    fetch("/cursos/obtener_cursos_json/")
        .then(handleResponse)
        .then(displayCourses)
        .catch(handleError);
}

// Función para mostrar la lista de módulos en la interfaz
function displayModules(modules) {
    const listaModulos = document.getElementById("lista-modulos");
    listaModulos.innerHTML = "";

    if (modules.length === 0) {
        listaModulos.innerHTML = '<div class="text-[10px] font-bold text-slate-400 p-2 italic">Sin módulos.</div>';
        return;
    }

    modules.forEach(modulo => {
        const li = document.createElement("li");
        li.className = "module-item flex items-center gap-3 p-3 text-slate-500 font-bold hover:bg-slate-50 rounded-xl transition-all cursor-pointer group border-2 border-transparent";
        li.innerHTML = `
            <div class="w-2 h-2 rounded-full bg-slate-200 group-hover:bg-primary transition-colors"></div>
            <span class="text-xs truncate">${modulo.nombre}</span>
        `;
        li.dataset.moduleId = modulo.id;

        // Handler para selección de módulo
        li.addEventListener("click", (e) => {
            selectModule(modulo.id, modulo.nombre, e.currentTarget);
        });

        listaModulos.appendChild(li);
    });

    document.getElementById("seccion-modulos").classList.remove("hidden");
}
window.displayModules = displayModules;

// Función para seleccionar un módulo
window.selectModule = function (moduleId, moduleName, element) {
    console.log("Seleccionando módulo:", moduleId, moduleName);
    selectedModuleId = moduleId;
    selectedModuleName = moduleName;

    // Resetear selección en el sidebar de módulos
    document.querySelectorAll(".module-item").forEach(item => {
        item.classList.remove("active", "bg-blue-600", "text-white", "border-yellow-400");
        item.classList.add("text-slate-500", "hover:bg-slate-50", "border-transparent");

        // Reset dot
        const dot = item.querySelector('.w-2');
        if (dot) dot.classList.replace('bg-white', 'bg-slate-200');
    });

    // Resaltar elemento seleccionado (SI es un item del sidebar/module-item)
    if (element.classList.contains('module-item')) {
        element.classList.remove("text-slate-500", "hover:bg-slate-50", "border-transparent");
        element.classList.add("active", "bg-blue-600", "text-white", "border-yellow-400");

        const dot = element.querySelector('.w-2');
        if (dot) dot.classList.replace('bg-slate-200', 'bg-white');
    }

    // Mostrar opciones del módulo en el sidebar (opcional si se usa el dashboard)
    document.getElementById("opciones-modulo")?.classList.remove("hidden");

    // Cargar el Dashboard central del módulo
    renderModuloDashboard(moduleId);
}

// Nueva función para renderizar el dashboard central del módulo
window.renderModuloDashboard = function (moduleId) {
    const container = document.getElementById('datos-curso');

    container.innerHTML = `
        <div class="bg-white rounded-[2.5rem] p-12 text-center border border-slate-100 shadow-sm animate-pulse">
            <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 text-green-500">
                <i class="fas fa-circle-notch fa-spin text-4xl"></i>
            </div>
            <h2 class="text-2xl font-black text-slate-800 mb-2">Cargando Módulo...</h2>
            <p class="text-slate-400 font-medium">Obteniendo detalles del módulo.</p>
        </div>
    `;

    fetch(`/cursos/obtener-datos-modulo/${moduleId}/`)
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener datos");
            return response.json();
        })
        .then(data => {
            container.innerHTML = `
                <div class="space-y-8 animate-fade-in">
                    <!-- Header del Módulo -->
                    <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl shadow-slate-200/40 relative overflow-hidden">
                        <div class="absolute top-0 right-0 w-32 h-32 bg-green-500/5 rounded-bl-[5rem] -mr-8 -mt-8"></div>
                        <div class="relative z-10">
                            <span class="px-4 py-1.5 bg-green-100 text-green-600 text-[10px] font-black uppercase tracking-widest rounded-full mb-4 inline-block">
                                Módulo del Curso
                            </span>
                            <h1 class="text-4xl font-black text-slate-800 leading-tight mb-4">${data.nombre}</h1>
                            <p class="text-slate-500 font-medium max-w-2xl mb-8">${data.descripcion || 'Sin descripción disponible.'}</p>
                            
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="p-4 bg-slate-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Carga Horaria</p>
                                    <p class="text-xl font-black text-slate-800">${data.carga_horaria} hs</p>
                                </div>
                                ${(() => {
                    const total = data.total_estudiantes || 0;
                    const calificados = data.estudiantes_con_nota || 0;
                    const faltantes = total - calificados;

                    let bgClass, textClass, titleClass, statusText;

                    if (total === 0) {
                        bgClass = 'bg-slate-50';
                        textClass = 'text-slate-400';
                        titleClass = 'text-slate-400';
                        statusText = 'Sin estudiantes';
                    } else if (faltantes === 0) {
                        bgClass = 'bg-emerald-50';
                        textClass = 'text-emerald-600';
                        titleClass = 'text-emerald-400';
                        statusText = 'Completado';
                    } else {
                        bgClass = 'bg-rose-50';
                        textClass = 'text-rose-600';
                        titleClass = 'text-rose-400';
                        statusText = `Falta ${faltantes} de ${total}`;
                    }

                    return `
                                        <div class="p-4 ${bgClass} rounded-2xl">
                                            <p class="text-[10px] font-black uppercase tracking-widest ${titleClass} mb-1">Estado</p>
                                            <p class="text-xl font-black ${textClass}">
                                                ${statusText}
                                            </p>
                                        </div>
                                    `;
                })()}
                                <div class="p-4 bg-blue-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-blue-400 mb-1">Inicio</p>
                                    <p class="text-xl font-black text-blue-600">${data.fecha_inicio}</p>
                                </div>
                                <div class="p-4 bg-rose-50 rounded-2xl">
                                    <p class="text-[10px] font-black uppercase tracking-widest text-rose-400 mb-1">Fin</p>
                                    <p class="text-xl font-black text-rose-600">${data.fecha_fin}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                        <!-- Detalles Adicionales -->
                        <div class="xl:col-span-2 space-y-6">
                            <h5 class="text-xl font-black text-slate-800 flex items-center gap-3">
                                <span class="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 text-sm">
                                    <i class="fas fa-info-circle"></i>
                                </span>
                                Información Detallada
                            </h5>
                            <div class="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm space-y-6">
                                <div>
                                    <h6 class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Cursos Vinculados</h6>
                                    <div class="flex flex-wrap gap-2">
                                        ${data.cursos_asociados.map(curso => `
                                            <span class="px-3 py-1 bg-slate-50 text-slate-600 text-xs font-bold rounded-lg border border-slate-100">
                                                ${curso}
                                            </span>
                                        `).join('')}
                                    </div>
                                </div>
                                
                                ${data.recursos_url ? `
                                    <div class="p-4 bg-primary/5 rounded-2xl flex items-center justify-between">
                                        <div class="flex items-center gap-3">
                                            <i class="fas fa-file-pdf text-2xl text-rose-500"></i>
                                            <div>
                                                <p class="text-sm font-black text-slate-800">Recursos del Módulo</p>
                                                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Documento PDF</p>
                                            </div>
                                        </div>
                                        <a href="${data.recursos_url}" target="_blank" class="px-4 py-2 bg-white text-primary text-xs font-black rounded-xl border border-primary/20 hover:bg-primary hover:text-white transition-all">
                                            DESCARGAR
                                        </a>
                                    </div>
                                ` : ''}
                            </div>
                        </div>

                        <!-- Acciones del Módulo -->
                        <div class="space-y-6">
                            <h5 class="text-xl font-black text-slate-800 flex items-center gap-3">
                                <span class="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center text-amber-600 text-sm">
                                    <i class="fas fa-graduation-cap"></i>
                                </span>
                                Gestión del Módulo
                            </h5>
                            <div class="bg-white rounded-[2rem] border border-slate-100 p-4 space-y-2">
                                <button onclick="handleVerNotas()"
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-star text-yellow-500 group-hover:scale-110 transition-transform"></i>
                                    Ver Calificaciones
                                </button>
                                <button onclick="window.location.href='/cursos/gestionar_notas/${moduleId}/'"
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-user-edit text-primary group-hover:scale-110 transition-transform"></i>
                                    Gestionar Notas
                                </button>
                                <button onclick="abrirModalEditarModulo(${moduleId})"
                                    class="w-full flex items-center gap-4 p-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all group">
                                    <i class="fas fa-folder-open text-amber-600 group-hover:scale-110 transition-transform"></i>
                                    Editar Módulo
                                </button>
                                <button onclick="eliminarModulo(${moduleId}, '${data.nombre}')"
                                    class="w-full flex items-center gap-4 p-4 text-rose-500 font-bold hover:bg-rose-50 rounded-2xl transition-all group">
                                    <i class="fas fa-trash-alt group-hover:scale-110 transition-transform"></i>
                                    Eliminar Módulo
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error("Error:", error);
            container.innerHTML = `<div class="p-8 bg-rose-50 text-rose-500 rounded-[2.5rem] font-bold text-center">Error al cargar el módulo: ${error.message}</div>`;
        });
}

// Helpers para módulos
function abrirModalEditarModulo(id) {
    const modal = document.getElementById("editarModuloModal");
    const content = document.getElementById("editarModuloContent");

    content.innerHTML = `
        <div class="flex items-center justify-center p-12">
            <i class="fas fa-circle-notch fa-spin text-4xl text-amber-500"></i>
        </div>
    `;
    modal.classList.remove("hidden");

    fetch(`/cursos/modulo/${id}/editar/`)
        .then(response => response.text())
        .then(html => {
            content.innerHTML = html;
        });
}

function eliminarModulo(id, nombre) {
    if (!confirm(`¿Estás seguro de que deseas eliminar el módulo "${nombre}"?`)) return;

    fetch(`/cursos/modulos/eliminar/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarToast(data.message, "success");
                // Recargar sidebar y dashboard
                fetchModules(selectedCourseId);
                renderCursoDashboard(selectedCourseId);
            } else {
                mostrarToast(data.error || "Error al eliminar", "danger");
            }
        })
        .catch(handleError);
}

// --------------------------------------------------------------------
// Funciones de estudiantes
// --------------------------------------------------------------------
// Función para formatear un número de teléfono
function formatPhoneNumber(phone) {
    // Eliminar espacios, guiones y caracteres no numéricos
    phone = phone.replace(/[^0-9]/g, "");

    // Validar y ajustar el formato
    if (phone.startsWith("+549")) {
        phone = phone.slice(4); // Eliminar +549
    } else if (phone.startsWith("549")) {
        phone = phone.slice(3); // Eliminar 549
    } else if (phone.startsWith("49")) {
        phone = phone.slice(2); // Eliminar 49
    } else if (phone.startsWith("911")) {
        phone = phone.slice(3); // Eliminar 911
    } else if (phone.startsWith("15")) {
        phone = phone.slice(2); // Eliminar 15
    } else if (phone.startsWith("015")) {
        phone = phone.slice(3); // Eliminar 015
    } else if (phone.startsWith("0")) {
        phone = phone.slice(1); // Eliminar 0 inicial
    }

    // Asegurarse de que comience con 11
    if (!phone.startsWith("11")) {
        phone = "11" + phone.slice(2); // Reemplazar los primeros dos dígitos con 11
    }

    // Limitar a 10 dígitos (11 + 8 dígitos restantes)
    return phone.length > 10 ? phone.slice(0, 10) : phone;
}

// Función para obtener la lista de estudiantes de un curso
window.fetchStudents = function (cursoId) {
    fetch(`/cursos/curso/${cursoId}/estudiantes/json/`)
        .then(handleResponse)
        .then(displayStudents)
        .catch(handleError);
}

// Variable global para almacenar los datos de la planilla
let estudiantesData = {};

// Función para mostrar la lista de estudiantes en la interfaz (DASHBOARD VERSION)
function displayStudents(data) {
    const container = document.getElementById('datos-curso');
    estudiantesData = data;

    // Ordenamos
    data.estudiantes.sort((a, b) => a.nombre.localeCompare(b.nombre));
    data.estudiantes_pen.sort((a, b) => a.nombre.localeCompare(b.nombre));

    container.innerHTML = `
        <div class="space-y-8 animate-fade-in">
            <div class="flex items-center justify-between mb-4">
                <button onclick="renderCursoDashboard(${selectedCourseId})" 
                    class="flex items-center gap-2 text-slate-400 hover:text-primary font-black text-[10px] uppercase tracking-widest transition-colors">
                    <i class="fas fa-arrow-left"></i> Volver al Dashboard
                </button>
                <button onclick="document.dispatchEvent(new Event('triggerExportAsistencia'))"
                    class="px-6 py-2.5 bg-primary text-white text-[10px] font-black uppercase tracking-widest rounded-xl shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all">
                    Exportar Planilla
                </button>
            </div>

            <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl shadow-slate-200/40">
                <h2 class="text-3xl font-black text-slate-800 mb-8 flex items-center gap-4">
                    <span class="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary">
                        <i class="fas fa-users"></i>
                    </span>
                    Listado de Estudiantes
                </h2>

                <div class="overflow-x-auto rounded-3xl border border-slate-50">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-slate-50/50">
                                <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Estudiante</th>
                                <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Contacto</th>
                                <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Último Acceso</th>
                                <th class="p-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            ${data.estudiantes.map(est => `
                                <tr class="hover:bg-slate-50/50 transition-colors">
                                    <td class="p-6">
                                        <div class="flex items-center gap-4">
                                            <div class="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 font-black text-sm">
                                                ${est.nombre.charAt(0)}
                                            </div>
                                            <div>
                                                <p class="font-black text-slate-800">${est.nombre}</p>
                                                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Estudiante Regular</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="p-6">
                                        <p class="text-sm font-bold text-slate-600 mb-1">${est.email}</p>
                                        ${est.telefono ? `
                                            <a href="https://wa.me/+549${formatPhoneNumber(est.telefono)}" target="_blank" 
                                               class="inline-flex items-center gap-1.5 text-emerald-500 font-black text-[10px] uppercase hover:underline">
                                                <i class="fab fa-whatsapp"></i> ${formatPhoneNumber(est.telefono)}
                                            </a>
                                        ` : '<span class="text-[10px] font-bold text-slate-300 italic">SIN TELÉFONO</span>'}
                                    </td>
                                    <td class="p-6">
                                        <span class="px-3 py-1 bg-slate-50 text-slate-500 text-[10px] font-black rounded-lg border border-slate-100">
                                            ${est.ultimo_login || 'NUNCA'}
                                        </span>
                                    </td>
                                    <td class="p-6 text-right whitespace-nowrap">
                                        <div class="flex items-center justify-end gap-2">
                                            <!-- Checkbox Pago -->
                                            <label class="flex items-center gap-1 cursor-pointer group/check" title="Marcar Pago Contribución">
                                                <input type="checkbox" 
                                                    class="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary/20 transition-all cursor-pointer"
                                                    ${est.pago_contribucion ? 'checked' : ''}
                                                    onchange="actualizarEstadoInscripcion(${est.inscripcion_id}, 'pago_contribucion', this.checked)">
                                                <span class="text-[9px] font-black uppercase tracking-tight text-slate-400 group-hover/check:text-primary transition-colors">Pago</span>
                                            </label>

                                            <!-- Checkbox Certificado -->
                                            <label class="flex items-center gap-1 cursor-pointer group/check mr-2" title="Marcar Entrega Planilla/Certificado">
                                                <input type="checkbox" 
                                                    class="w-4 h-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500/20 transition-all cursor-pointer"
                                                    ${est.entrega_certificado ? 'checked' : ''}
                                                    onchange="actualizarEstadoInscripcion(${est.inscripcion_id}, 'entrega_certificado', this.checked)">
                                                <span class="text-[9px] font-black uppercase tracking-tight text-slate-400 group-hover/check:text-emerald-500 transition-colors">Planilla</span>
                                            </label>

                                            <a href="/mensajes/chat/${est.id}/" 
                                                class="p-3 text-slate-400 hover:text-primary hover:bg-blue-50 rounded-xl transition-all inline-block"
                                                title="Enviar Mensaje Interno">
                                                <i class="fas fa-comment-dots"></i>
                                            </a>
                                            <button onclick="eliminarEstudiante(${est.id})"
                                                class="p-3 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                                                title="Eliminar Estudiante">
                                                <i class="fas fa-trash-alt"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}

                            ${data.estudiantes_pen.map(est => `
                                <tr class="hover:bg-slate-50/50 transition-colors">
                                    <td class="p-6">
                                        <div class="flex items-center gap-4">
                                            <div class="w-10 h-10 bg-amber-50 rounded-full flex items-center justify-center text-amber-500 font-black text-sm border border-amber-100">
                                                <i class="fas fa-user-shield"></i>
                                            </div>
                                            <div>
                                                <p class="font-black text-slate-800">${est.nombre}</p>
                                                <p class="text-[10px] font-bold text-amber-400 uppercase tracking-widest">Estudiante PEN</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="p-6">
                                        <p class="text-[10px] font-black text-slate-400 mb-1 uppercase tracking-widest">DNI</p>
                                        <p class="font-mono font-bold text-slate-600">${est.dni}</p>
                                    </td>
                                    <td class="p-6">
                                        <span class="px-3 py-1 bg-slate-50 text-slate-300 text-[10px] font-black rounded-lg italic">
                                            NO DISPONIBLE
                                        </span>
                                    </td>
                                    <td class="p-6 text-right whitespace-nowrap">
                                        <button onclick="eliminarEstudiantePen('${est.dni}')"
                                            class="p-3 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                                            title="Eliminar Estudiante">
                                            <i class="fas fa-trash-alt"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

// Event listener helper para exportar asistencia desde el dashboard
document.addEventListener('triggerExportAsistencia', () => {
    if (!selectedCourseId) return mostrarToast("Selecciona un curso primero", "warning");
    crearModalSeleccionMes();
    document.getElementById("modalSeleccionMes").classList.remove("hidden");
});

document.addEventListener("click", function (e) {
    const btn = e.target.closest('[data-action="exportar-asistencia"]');
    if (btn) {
        if (!selectedCourseId) {
            mostrarToast("Seleccioná un curso primero", "warning");
            return;
        }

        crearModalSeleccionMes();
        document.getElementById("modalSeleccionMes").classList.remove("hidden");
    }

    if (e.target.id === "btnExportarAsistencia") {
        const mes = parseInt(document.getElementById("mesSeleccionado").value);
        document.getElementById("modalSeleccionMes").classList.add("hidden");

        fetch(`/cursos/asistencia_mes/${selectedCourseId}/${mes}/`)
            .then(res => res.json())
            .then(data => {
                const estudiantes = data.estudiantes;
                const dias = data.dias;

                let csv = "\uFEFFN°,Nombre,DNI," + dias.join(",") + "\n";


                estudiantes.forEach((est, i) => {
                    const fila = [
                        i + 1,
                        est.nombre,
                        est.dni,
                        ...dias.map(dia => est.asistencias[dia] || "")
                    ];
                    csv += fila.join(",") + "\n";
                });

                const link = document.createElement("a");
                link.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
                const fecha = new Date();
                link.download = `asistencia_mes_${mes}_${fecha.getFullYear()}.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            })
            .catch(err => {
                console.error("Error al exportar asistencia:", err);
                mostrarToast("Error al exportar la asistencia", "danger");
            });
    }
});


// Función para eliminar un estudiante penitenciario
window.eliminarEstudiantePen = function (dni) {
    if (!confirm("¿Confirmar eliminación del estudiante penitenciario?")) return;

    fetch(`/cursos/curso/${selectedCourseId}/eliminar_estudiante_pen_curso/${dni}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
        },
    })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                mostrarToast(data.message, "success");
                document.querySelector(`[data-dni="${dni}"]`).closest("tr").remove();

                // Mostrar pop-up bonito con SweetAlert2
                Swal.fire({
                    title: "⚠️ Aviso",
                    text: "Recuerda avisar a los administradores sobre esta eliminación.",
                    icon: "warning",
                    confirmButtonText: "Entendido"
                });
            }
        })
        .catch(handleError);
}

// Función para eliminar un estudiante regular
window.eliminarEstudiante = function (estudianteId) {
    Swal.fire({
        title: 'Motivo de eliminación',
        input: 'text',
        inputLabel: 'Por favor, indique el motivo por el cual elimina al estudiante',
        inputPlaceholder: 'Ingrese el motivo aquí...',
        showCancelButton: true,
        confirmButtonText: 'Eliminar',
        cancelButtonText: 'Cancelar',
        inputValidator: (value) => {
            if (!value || value.trim() === '') {
                return '¡Debe ingresar un motivo para poder eliminar al estudiante!'
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const motivo = result.value;
            fetch(`/cursos/curso/${selectedCourseId}/eliminar_estudiante/${estudianteId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ motivo: motivo })
            })
                .then(response => {
                    if (!response.ok) throw new Error(`Error ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        mostrarToast(data.message, "success");
                        // Asumiendo que existe el data-estudiante-id o lo eliminamos padre del button
                        const elem = document.querySelector(`[data-estudiante-id="${estudianteId}"]`);
                        if (elem) {
                            elem.closest("tr").remove();
                        } else {
                            // En fallback re-renderizamos la vista de estudiantes
                            fetchStudents(selectedCourseId);
                        }
                    } else {
                        mostrarToast(data.error || "Hubo un error", "danger");
                    }
                })
                .catch(handleError);
        }
    });
}

// --------------------------------------------------------------------
// Funciones auxiliares
// --------------------------------------------------------------------
// Función para manejar la respuesta de una solicitud
function handleResponse(response) {
    if (!response.ok) throw new Error(`Error ${response.status}`);
    return response.json();
}

// Función para manejar errores
function handleError(error) {
    console.error("Error:", error);
    mostrarToast(error.message || "Error en la operación", "danger");
}

// Función para obtener el valor de una cookie
function getCookie(name) {
    return document.cookie.match(`(^|;)\\s*${name}\\s*=\\s*([^;]+)`)?.pop() || '';
}

// Función para mostrar un mensaje tipo toast
// Función para mostrar un mensaje tipo toast (Versión Tailwind)
function mostrarToast(mensaje, tipo = "success") {
    const toastId = 'toast-' + Date.now();
    const colors = {
        success: 'bg-emerald-500',
        danger: 'bg-rose-500',
        warning: 'bg-amber-500',
        info: 'bg-blue-500'
    };
    const icon = {
        success: '<i class="fas fa-check-circle"></i>',
        danger: '<i class="fas fa-exclamation-circle"></i>',
        warning: '<i class="fas fa-exclamation-triangle"></i>',
        info: '<i class="fas fa-info-circle"></i>'
    };

    const toastHtml = `
        <div id="${toastId}" class="flex items-center w-full max-w-xs p-4 mb-4 text-white ${colors[tipo] || colors.info} rounded-2xl shadow-xl transform translate-y-10 opacity-0 transition-all duration-300 ease-out" role="alert">
            <div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-white rounded-lg bg-white/20">
                ${icon[tipo] || icon.info}
            </div>
            <div class="ml-3 text-sm font-bold">${mensaje}</div>
            <button type="button" class="ml-auto -mx-1.5 -my-1.5 bg-transparent text-white rounded-lg focus:ring-2 focus:ring-white/50 p-1.5 hover:bg-white/20 inline-flex items-center justify-center h-8 w-8" data-dismiss-target="#${toastId}" aria-label="Close" onclick="document.getElementById('${toastId}').remove()">
                <span class="sr-only">Cerrar</span>
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2';
        document.body.appendChild(container);
    }

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = toastHtml.trim();
    const toastElement = tempDiv.firstChild;
    container.appendChild(toastElement);

    // Animación de entrada
    requestAnimationFrame(() => {
        toastElement.classList.remove('translate-y-10', 'opacity-0');
    });

    // Auto eliminar
    setTimeout(() => {
        if (toastElement && document.body.contains(toastElement)) {
            toastElement.classList.add('opacity-0', 'translate-y-10');
            setTimeout(() => toastElement.remove(), 300);
        }
    }, 4000);
}

// --------------------------------------------------------------------
// Funcionalidad de Clases
// --------------------------------------------------------------------
document.addEventListener("click", function (e) {

    // Ver Clases
    if (e.target.closest('[data-action="ver-clases"]')) {
        if (!selectedCourseId) {
            mostrarToast("Selecciona un curso primero", "warning");
            return;
        }

        fetch(`/cursos/ver_clases/${selectedCourseId}/`)
            .then(response => response.text())
            .then(html => {
                const modal = document.getElementById("verClasesModal");
                const modalContent = document.getElementById("verClasesModalContent");
                modalContent.innerHTML = html;
                modal.classList.remove("hidden");
            })
            .catch(handleError);
    }

});
document.addEventListener("click", function (e) {
    const btnNotas = e.target.closest('[data-action="ver-notas"]');
    if (btnNotas) {
        console.log("👉 Acción: ver-notas");
        console.log("Curso seleccionado:", selectedCourseId);
        console.log("Módulo seleccionado:", selectedModuleId);

        if (!selectedCourseId) {
            mostrarToast("Selecciona un curso primero", "warning");
            return;
        }

        if (!selectedModuleId) {
            mostrarToast("Selecciona un módulo primero", "warning");
            return;
        }

        fetch(`/cursos/${selectedCourseId}/notas/`)
            .then(response => {
                if (!response.ok) throw new Error(`Error ${response.status}`);
                return response.json();
            })
            .then(data => {
                const container = document.getElementById("notas-content");
                container.innerHTML = data.notas.length ?
                    generarListaNotas(data.notas) :
                    "<p>No hay notas registradas</p>";
                container.classList.remove("d-none");
            })
            .catch(error => {
                mostrarToast("Error al cargar las notas", "danger");
                console.error("Error:", error);
            });
    }
});

document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-action="gestionar-notas"]');
    if (btn) {
        console.log("🟢 Botón 'Gestionar Notas' clickeado");
        console.log("➡️ Módulo ID:", selectedModuleId);

        if (selectedModuleId) {
            window.location.href = `/cursos/gestionar_notas/${selectedModuleId}/`;
        } else {
            mostrarToast("Selecciona un módulo primero", "warning");
        }
    }
});


function generarListaNotas(notas) {
    return `
        <div class="space-y-6 animate-fade-in">
            <h5 class="text-xl font-black text-slate-800 flex items-center gap-3">
                <span class="w-8 h-8 bg-yellow-50 rounded-lg flex items-center justify-center text-yellow-600 text-sm">
                    <i class="fas fa-star"></i>
                </span>
                Calificaciones del Módulo
            </h5>
            <div class="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden">
                <div class="divide-y divide-slate-50">
                    ${notas.map(nota => `
                        <div class="p-6 flex items-center justify-between hover:bg-slate-50 transition-colors">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 font-black text-xs">
                                    ${nota.estudiante.charAt(0)}
                                </div>
                                <div>
                                    <p class="font-black text-slate-800">${nota.estudiante}</p>
                                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">${nota.modulo}</p>
                                </div>
                            </div>
                            <span class="px-4 py-2 bg-primary/10 text-primary rounded-xl font-black text-sm">
                                ${nota.nota}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}
// --------------------------------------------------------------------
// Funcionalidad: Ver Detalles del Curso
// --------------------------------------------------------------------
document.addEventListener("click", function (e) {
    if (e.target.closest('[data-action="detalles-curso"]')) {
        if (!selectedCourseId) {
            mostrarToast("Selecciona un curso primero", "warning");
            return;
        }

        const url = `/cursos/obtener-datos-curso/${selectedCourseId}/`;
        const contenedor = document.getElementById('datos-curso');

        // Mostrar estado de carga
        contenedor.innerHTML = `
            <div class="d-flex align-items-center text-primary my-4">
                <div class="spinner-border me-2" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                Cargando detalles del curso...
            </div>
        `;

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                contenedor.innerHTML = crearVistaDetallesCurso(data);
            })
            .catch(error => {
                contenedor.innerHTML = `
                    <div class="alert alert-danger mt-3">
                        ⚠️ Error al cargar los detalles: ${error.message}
                    </div>
                `;
            });
    }
});

function crearVistaDetallesCurso(data) {
    return `
        <div class="space-y-8 animate-fade-in">
            <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl shadow-slate-200/40 relative overflow-hidden">
                <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[5rem] -mr-8 -mt-8"></div>
                <div class="relative z-10">
                    <h1 class="text-4xl font-black text-slate-800 leading-tight mb-8">${data.nombre}</h1>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div class="space-y-6">
                            <h6 class="text-[10px] font-black uppercase tracking-widest text-primary flex items-center gap-2">
                                <i class="fas fa-info-circle"></i> Información del Curso
                            </h6>
                            <div class="space-y-4">
                                <div class="flex justify-between items-center p-4 bg-slate-50 rounded-2xl">
                                    <span class="text-xs font-bold text-slate-500">Fecha de Inicio</span>
                                    <span class="px-3 py-1 bg-white text-primary text-xs font-black rounded-lg shadow-sm">${data.fecha_inicio}</span>
                                </div>
                                <div class="flex justify-between items-center p-4 bg-slate-50 rounded-2xl">
                                    <span class="text-xs font-bold text-slate-500">Fecha de Fin</span>
                                    <span class="px-3 py-1 bg-white text-primary text-xs font-black rounded-lg shadow-sm">${data.fecha_fin}</span>
                                </div>
                                <div class="flex justify-between items-center p-4 bg-slate-50 rounded-2xl">
                                    <span class="text-xs font-bold text-slate-500">Cupo Disponible</span>
                                    <span class="px-3 py-1 bg-white text-emerald-600 text-xs font-black rounded-lg shadow-sm">${data.vacantes_disponibles} de ${data.max_estudiantes}</span>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-6">
                            <h6 class="text-[10px] font-black uppercase tracking-widest text-blue-500 flex items-center gap-2">
                                <i class="fas fa-user-tie"></i> Equipo Docente
                            </h6>
                            <div class="bg-slate-50 p-6 rounded-2xl flex items-center gap-4">
                                <div class="w-16 h-16 bg-white rounded-full flex items-center justify-center text-slate-300 shadow-sm border border-slate-100">
                                    <i class="fas fa-user-circle text-4xl"></i>
                                </div>
                                <div>
                                    <p class="font-black text-slate-800">${data.instructor.apellido}</p>
                                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">${data.instructor.email}</p>
                                    <p class="mt-1 text-[9px] font-black text-primary uppercase bg-primary/10 px-2 py-0.5 rounded-md inline-block">ID: ${data.instructor.username}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="flex justify-center">
                <button onclick="renderCursoDashboard(${selectedCourseId})"
                    class="flex items-center gap-2 px-8 py-4 bg-slate-900 text-white rounded-2xl font-black shadow-xl shadow-slate-900/20 hover:bg-black transition-all active:scale-95 text-[10px] uppercase tracking-widest text-sm">
                    <i class="fas fa-arrow-left"></i> Volver al Dashboard
                </button>
            </div>
        </div>
    `;
}

document.addEventListener("click", function (e) {
    if (e.target.closest('[data-action="crear-curso"]')) {
        window.location.href = "/cursos/crear/"; // Redirige a la función crear_curso
    }
});

document.addEventListener("click", function (e) {
    if (e.target.closest('[data-action="crear-modulo"]')) {
        window.location.href = "/cursos/modulos/crear"; // Redirige a la función crear_curso
    }
});


// Insertar el modal dinámicamente si no existe
function crearModalSeleccionMes() {
    if (document.getElementById("modalSeleccionMes")) return;

    const modalHtml = `
        <div id="modalSeleccionMes" class="fixed inset-0 z-[100] hidden overflow-y-auto">
            <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onclick="this.parentElement.classList.add('hidden')"></div>
            <div class="flex min-h-full items-center justify-center p-4">
                <div class="relative w-full max-w-md bg-white rounded-[2.5rem] shadow-2xl overflow-hidden p-10 animate-zoom-in">
                    <h3 class="text-2xl font-black text-slate-800 mb-6">Exportar Asistencia</h3>
                    
                    <div class="space-y-4 mb-8">
                        <div>
                            <label for="mesSeleccionado" class="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 ml-1">Seleccionar Mes</label>
                            <select id="mesSeleccionado" class="w-full p-4 bg-slate-50 border-none rounded-2xl font-bold text-slate-600 focus:ring-2 focus:ring-primary/20 transition-all outline-none appearance-none">
                                ${[...Array(10).keys()].map(i => {
        const mes = i + 3;
        return `<option value="${mes}">${new Date(2024, mes - 1).toLocaleString('es-AR', { month: 'long' })}</option>`;
    }).join("")}
                            </select>
                        </div>
                    </div>

                    <div class="flex gap-4">
                        <button type="button" 
                            class="flex-1 py-4 bg-slate-100 text-slate-600 font-bold rounded-2xl hover:bg-slate-200 transition-all"
                            onclick="document.getElementById('modalSeleccionMes').classList.add('hidden')">Cancelar</button>
                        <button type="button" id="btnExportarAsistencia"
                            class="flex-1 py-4 bg-primary text-white font-black rounded-2xl hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all active:scale-95">
                            Exportar
                        </button>
                    </div>

                    <button type="button" class="absolute top-8 right-8 text-slate-400 hover:text-slate-600"
                        onclick="document.getElementById('modalSeleccionMes').classList.add('hidden')">
                        <i class="fas fa-times text-2xl"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHtml);
}

/**
 * Actualiza el estado de una inscripción (pago o certificado) vía AJAX.
 */
window.actualizarEstadoInscripcion = function (inscripcionId, campo, valor) {
    if (!inscripcionId) {
        mostrarToast("No se pudo identificar la inscripción.", "danger");
        return;
    }

    const formData = new FormData();
    formData.append('campo', campo);
    formData.append('valor', valor);

    fetch(`/cursos/inscripcion/actualizar-estado/${inscripcionId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarToast(data.message, "success");
            } else {
                mostrarToast(data.error || "Error al actualizar", "danger");
                // Revertir el checkbox si hubo error (opcional, requeriría recarga o manejo de estado)
            }
        })
        .catch(error => {
            console.error("Error:", error);
            mostrarToast("Error de conexión", "danger");
        });
}

