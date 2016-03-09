window.modal = {
    nextId: 0,
    modals: {},
    close: function(id) {
        if (modal.modals[id]) {
            modal.modals[id].modal('hide');
        }
    },
    setHeight: function(id, height) {
        if (this.modals[id]) {
            this.modals[id].find("iframe").css("height", height);
        }
    },
    add: function(modal) {
        var id = modal.attr("id") || ("m" + window.modalId++);
        this.modals[id] = modal;
        return id;
    }
};

$(function(){

    var addIdToHash = function(url, id) {
        return url + (url.indexOf("#") ? "#":";") + "id=" + id;
    };

    modalOpeners = $("[data-toggle='modal'][data-modal-href], [data-toggle='modal'][href]");
    console.log("modalOpeners",modalOpeners);
    if (modalOpeners.length) {
        var modalHost = $("#modalhost");
        var container = modalHost.find(".modal-content");
        var iframe = container.find("iframe");
        var id = modal.add(modalHost);
        iframe.load(function(){
            var loc = iframe.get(0).contentDocument.location;
            if (loc.href != "about:blank" && !/[#;]id=[^;]/.exec(loc.hash)) {
                loc.hash = addIdToHash(loc.hash, id);
            }
        });

        modalOpeners.each(function(){
            var link = $(this);
            link.click(function(event){
                console.log("clicked", link, iframe);
                var url = link.attr("href") || link.attr("data-modal-href");
                url = addIdToHash(url, id);
                console.log(url);
                iframe.attr("src", url);
            });
        });
    }
});