
const estado = document.getElementById("estado");
const resultado = document.getElementById("resultado");

async function cargarProductos() {
    estado.textContent = "Conectando con el backend...";
    resultado.replaceChildren();

    try {
        const respuesta = await fetch("http://localhost:9000/productos");

        if (!respuesta.ok) {
            throw new Error("Error HTTP: " + respuesta.status);
        }

        const productos = await respuesta.json();

        estado.textContent = "Productos encontrados: " + productos.length;

        productos.forEach((producto) => {
            const tarjeta = document.createElement("div");
            const nombre = document.createElement("h3");
            const precio = document.createElement("p");
            const cantidad = document.createElement("p");

            nombre.textContent = producto.nombre;
            precio.textContent = "Precio: " + producto.precio.toFixed(2) + " €";
            cantidad.textContent = "Cantidad: " + producto.cantidad;

            tarjeta.append(nombre, precio, cantidad);
            resultado.appendChild(tarjeta);
        });
    } catch (error) {
        estado.textContent = "No se pudieron cargar los productos.";
        console.error(error);
    }
}

cargarProductos();
