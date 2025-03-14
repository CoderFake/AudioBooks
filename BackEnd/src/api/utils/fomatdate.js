const formateDate = (birthdate) => {
    const dateParts = birthdate.split("/");
    const formattedDate = new Date(
        Date.UTC(dateParts[2], dateParts[1] - 1, dateParts[0])
    );
    return formattedDate;
};
module.exports = { formateDate };
