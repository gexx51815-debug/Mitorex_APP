
const estado = document.getElementById("estado");
const resultado = document.getElementById("resultado");

async function cargarNegocios() {

    estado.textContent = "Cargando negocios...";
    resultado.replaceChildren();

    try {

        const respuesta = await fetch(
            "http://localhost:9000/negocios"
        );

        if (!respuesta.ok) {
            throw new Error("Error HTTP: " + respuesta.status);
        }

        const negocios = await respuesta.json();

        estado.textContent =
            "Negocios encontrados: " + negocios.length;

        negocios.forEach((negocio) => {

            const tarjeta = document.createElement("article");
            tarjeta.className = "tarjeta-negocio";

            const botonNombre = document.createElement("button");
            botonNombre.textContent = negocio.nombre;
            botonNombre.className = "boton-negocio";

            botonNombre.addEventListener("click", () => {
                alert("Has seleccionado: " + negocio.nombre);
            });

            const categoria = document.createElement("p");
            categoria.textContent = "Categoría: " + negocio.categoria;

            const ubicacion = document.createElement("p");
            ubicacion.textContent = "Ubicación: " + negocio.ubicacion;

            const descripcion = document.createElement("p");
            descripcion.textContent = negocio.descripcion;

            const contacto = document.createElement("p");
            contacto.className = "contacto";

            contacto.textContent =
                "Teléfono: " + (negocio.telefono || "No disponible") +
                " | Correo: " + (negocio.correo || "No disponible");

            tarjeta.append(
                botonNombre,
                categoria,
                ubicacion,
                descripcion,
                contacto
            );

            resultado.appendChild(tarjeta);

        });

    } catch (error) {

        estado.textContent = "No se pudieron cargar los negocios.";

        console.error(error);

    }
}

cargarNegocios();
