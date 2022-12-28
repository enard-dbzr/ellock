var socket = io();

socket.on("refresh", function() {
    location.reload();
});

$(".accept_tg").click(function(obj) {
    var tg_id = obj.target.id.replace("tg_", "");
    socket.emit("accept_tg", tg_id);
});

$(".reject_tg").click(function(obj) {
    var tg_id = obj.target.id.replace("tg_", "");
    socket.emit("reject_tg", tg_id);
});
