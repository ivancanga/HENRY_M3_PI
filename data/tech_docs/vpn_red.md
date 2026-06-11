# VPN y Conectividad — IT Support

## Qué es la VPN corporativa

La VPN (red privada virtual) crea un túnel cifrado entre el dispositivo del empleado
y la red interna de la empresa. Se usa para acceder de forma segura a sistemas
internos que no están expuestos a internet, especialmente cuando se trabaja de forma
remota o desde redes no confiables. Todos los empleados remotos tienen el cliente de
VPN instalado en su notebook corporativa durante el onboarding.

## Cuándo usar la VPN

Es obligatorio usar la VPN para acceder a sistemas internos, repositorios de código,
bases de datos administrativas y cualquier recurso que maneje información sensible.
No es necesario usar la VPN para herramientas SaaS públicas que ya cuentan con SSO,
aunque se recomienda mantenerla activa cuando se trabaja desde redes Wi-Fi públicas.

Trabajar con información confidencial en una red pública (cafés, aeropuertos) sin
VPN está prohibido por la política de seguridad.

## Cómo conectarse

Para conectarse, el empleado abre el cliente de VPN, inicia sesión con su cuenta
corporativa y confirma el segundo factor (MFA). Una vez establecida la conexión, el
indicador del cliente muestra el estado "conectado". Si la conexión falla, conviene
verificar la conexión a internet, reiniciar el cliente y, si persiste, abrir un
ticket con IT Support.

## Rendimiento y servidores

La VPN ofrece varios servidores en distintas regiones. El cliente selecciona
automáticamente el servidor más cercano para optimizar la velocidad, pero el
empleado puede elegir otro manualmente si experimenta lentitud. Si la conexión es
muy lenta, suele ayudar cambiar de servidor o reconectarse.

## Red de oficina

En las oficinas existen dos redes Wi-Fi: la red corporativa, para dispositivos de la
empresa, y la red de invitados, para visitantes y dispositivos personales. Los
dispositivos personales de los empleados deben conectarse a la red de invitados,
nunca a la corporativa. La red corporativa ya está dentro del perímetro seguro, por
lo que no requiere VPN dentro de la oficina.

## Acceso de invitados

Los visitantes reciben credenciales temporales para la red de invitados, que expiran
automáticamente al final del día. El empleado anfitrión solicita el acceso de
invitado mediante el portal de IT Support con anticipación.

## Problemas comunes de conectividad

Cuando hay problemas de conexión, los pasos recomendados son: verificar el cable o
la señal Wi-Fi, reiniciar el router doméstico, comprobar que la VPN esté conectada y
revisar si hay una interrupción reportada en el portal de estado de servicios. La
mayoría de los problemas se resuelven reiniciando el cliente de VPN o el equipo.

## Interrupciones del servicio

Cuando ocurre una interrupción que afecta a varios empleados, IT Support la publica
en el portal de estado de servicios y en el canal de Slack de incidentes. Antes de
abrir un ticket por un problema de conectividad general, conviene revisar si ya hay
una interrupción conocida en curso.

## Preguntas frecuentes

¿Tengo que usar la VPN dentro de la oficina? No, la red corporativa de la oficina ya
es segura. La VPN es necesaria fuera de la oficina.

¿Por qué mi VPN está lenta? Probá cambiar de servidor a uno más cercano o
reconectarte. Si persiste, abrí un ticket.

¿Puedo conectar mi celular personal a la red corporativa? No, los dispositivos
personales se conectan a la red de invitados.
