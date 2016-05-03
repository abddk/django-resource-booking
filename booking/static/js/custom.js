//Search-list.html start:
$('.collapse').on('show.bs.collapse', function() {
    $(this).parent().find(".caret").addClass("caret-up");
});
$('.collapse').on('hide.bs.collapse', function() {
    $(this).parent().find(".caret").removeClass("caret-up");
});
$('#filters').on('show.bs.collapse', function() {
    $(this).prev().find(".glyphicon").toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
});
$('#filters').on('hide.bs.collapse', function() {
    $(this).prev().find(".glyphicon").toggleClass("glyphicon-chevron-up glyphicon-chevron-down");
});

//Search-list.html end
$("#reset-btn").click(function() {
    $("#searchBox").val("");
    $("form").trigger("submit")
});

// Automatically submit the search form whenever the filters are changed
$(function() {
    $('#filter-search-results input[type=checkbox]').on('change', function() {
        $(this.form).trigger("submit")
    });
    $('#filter-search-results input.datepicker').on('changeDate', function() {
        $(this.form).trigger("submit")
    });
});
// Show/hide multiple dates
if ($("#dato li").data('expired', 'true').length > 1) {
    var dato = $("#dato"),
        showmore = "Vis flere datoer",
        showless = "Vis færre datoer";
    dato.find('[data-expired="true"]').hide();
    dato.after("<a href=\"#\" class=\"showhide\">"+showmore+"</a>");
    $(".showhide").click(function(e) {
        e.preventDefault();
        $("#dato").find('[data-expired="true"]').toggle(400);
        ($(this).text() === showmore) ? $(this).text(showless): $(this).text(showmore);
    });
}
