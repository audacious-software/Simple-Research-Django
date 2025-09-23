requirejs.config({
    shim: {
        jquery: {
            exports: "$"
        },
        cookie: {
            exports: "Cookies"
        },
        bootstrap: {
            deps: ["jquery"]
        },
    },
    baseUrl: "/static/simple_dashboard/js/app",
    paths: {
        app: '/static/simple_dashboard/js/app',
        material: "/static/simple_dashboard/js/vendor/material-components-web-11.0.0",
        jquery: "/static/simple_dashboard/js/vendor/jquery-3.4.0.min",
        cookie: "/static/simple_dashboard/js/vendor/js.cookie"
    }
});

requirejs(["material", "cookie", "jquery", "base"], function(mdc, Cookies) {
	const doSearch = function(query) {
		const url = URL.parse(window.location.href)
		url.searchParams.set('limit', select.value)
		url.searchParams.set('offset', '0')
		url.searchParams.set('q', query)

		window.location.href = url.href
	}

	const searchField = mdc.textField.MDCTextField.attachTo(document.getElementById('topbar_search'));

	$('#topbar_search_field').on('keypress', function(eventObj) {
		if (eventObj.which == 13) {
			eventObj.preventDefault();

			doSearch(searchField.value)
		}
	})

	$('#topbar_search_icon').on('click', function(eventObj) {
		doSearch(searchField.value)
	})

	mdc.dataTable.MDCDataTable.attachTo(document.getElementById('studies_table'));

	const select = mdc.select.MDCSelect.attachTo(document.querySelector('.mdc-select'));

	const url = URL.parse(window.location.href)

	if (url.searchParams.get('limit') !== null) {
		select.value = url.searchParams.get('limit')
	} else {
		select.value = '25'
	}

	if (url.searchParams.get('q') !== null) {
		searchField.value = url.searchParams.get('q')
	}

	select.listen('MDCSelect:change', () => {
		const url = URL.parse(window.location.href)
		url.searchParams.set('limit', select.value)
		window.location.href = url.href
	});

	const addStudy = mdc.dialog.MDCDialog.attachTo(document.getElementById('add_study_dialog'));

	const deleteStudy = mdc.dialog.MDCDialog.attachTo(document.getElementById('confirm_delete_study'));

	const addStudyName = mdc.textField.MDCTextField.attachTo(document.getElementById('new_study_name'));

	$("#fab_add_study").click(function(eventObj) {
		addStudyName.value = '';

		$("#add-dialog-title").text('Add new study')
		$('#dialog_update_study_button .mdc-button__label').text('Add')
		$('#update_study_id').val('')

		addStudy.open();
	});

	$(".study_update_button").click(function(eventObj) {
		$("#add-dialog-title").text('Update study');

		const name = $(this).attr('data-edit-name')
		const id = $(this).attr('data-edit-id')
		const staff = $(this).attr('data-edit-staff').split(',')

		$('.checkbox-staff').prop('checked', false)

		staff.forEach(function(item) {
			$(`[id="checkbox-staff-${item}"]`).prop('checked', true)
		});

		addStudyName.value = name

		$('#update_study_id').val(id)
		$('#dialog_update_study_button .mdc-button__label').text('Update')

		addStudy.open()
	});

	$(".study_delete_button").click(function(eventObj) {
		$("#delete_study_name").text($(eventObj.target).data()["deleteName"]);
		$("#delete_study_id").val($(eventObj.target).data()["deleteId"]);

		deleteStudy.open()
	});

	deleteStudy.listen('MDCDialog:closed', function(event) {
		action = event.detail['action'];

		if (action == 'close') {

		} else if (action == 'delete') {
			var deleteId = $("#delete_study_id").val();

			$.post('/research/dashboard/study/delete.json', {
				'identifier': deleteId
			}, function(data) {
				if (data.message) {
					alert(data.message)
				}

				location.reload();
			});
		}
	});

	addStudy.listen('MDCDialog:closed', function(event) {
		action = event.detail['action'];

		if (action == 'close') {

		} else if (action == 'create') {
			let staffIds = []

			$('.checkbox-staff').each(function(item) {
				if ($(this).is(':checked')) {
					const id = $(this).attr('id').replace('checkbox-staff-', '')

					staffIds.push(id)
				}
			})

			$.post('/research/dashboard/study/update.json', {
				'name': addStudyName.value,
				'identifier': $('#update_study_id').val(),
				'staff_members': staffIds.join(',')
			}, function(data) {
				if (data.message) {
					alert(data.message)
				}

				location.reload();
			});
		}
	});

	$('.mdc-data-table__pagination-button').click(function(eventObj) {
		eventObj.preventDefault()

		const url = $(this).attr('data-url')

		window.location.href = url
	})
});